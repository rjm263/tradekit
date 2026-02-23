"""This module provides the Supervisor class.

This class is used for running engines on a server/cluster. It is crash-save and can orchestrate multiple engines (however, they must all be backtesting or all forward engines). It notifies the client about engine events such as crashes or finished runs.
"""

from tradekit.notifiers.base import Notifier
from tradekit.notifiers.events import Event
from tradekit.fees.factory import make_fee_model
from tradekit.metrics.blotter import TradeBlotter
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import signal
import time
import sys
import json
import os


class Supervisor:
    """This class provides a supervisor for running engines on a server.
    """    
    def __init__(self, backtesting: bool, name: str, engine_cfgs: dict, notifiers: list[Notifier] | None = None) -> None:
        """Initialises the Supervisor class.

        Parameters
        ----------
        backtesting : bool
            Specifies whether engines are instances of :class:`~tradekit.backtest_engine.engine.BacktestEngine` or :class:`~tradekit.forward_engine.engine.ForwardEngine`
        name : str
            The name of the supervisor; useful if multiple supervisors are in use
        engine_cfgs : dict
            The dictionary containing the names of engines as keys and paths to the resp. engine cfg files as values
        notifiers : list[Notifier] | None, optional
            The list of :class:`~tradekit.notifiers.base.Notifier` classes used to notify about updates, by default None
        """        
        self.backtesting = backtesting
        self.name = name
        self.engine_cfgs = engine_cfgs
        self.notifiers = notifiers or []
        self.processes = {}

    def start_engine(self, name: str, cfg_path: str) -> None:
        """Starts an engine process and adds it to the process registry.

        Parameters
        ----------
        name : str
            The name of the engine
        cfg_path : str
            The path to the engine configuration file
        """        
        if self.backtesting:
            p = subprocess.Popen([sys.executable, '-m', 'tradekit.backtest_engine', cfg_path])
        else:
            p = subprocess.Popen([sys.executable, '-m', 'tradekit.forward_engine', cfg_path])
        
        self.processes[name] = p
        print(f'Started engine {name} --> PID: {p.pid}')

    def stop_engine(self, name: str) -> None:
        """Stops an engine process from running.

        Parameters
        ----------
        name : str
            The name of the engine to be stopped
        """        
        p = self.processes.get(name)

        if p:
            p.send_signal(signal.SIGTERM)

    def shutdown(self) -> None:
        """Shuts down all running processes of the supervisor.
        """        
        for p in self.processes.values():
            p.send_signal(signal.SIGTERM)

        for p in self.processes.values():
            try:
                p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                p.kill()

    # ------------- Notifications -------------- #
    def _emit(self, type, source, payload=None, path_to_file=None) -> None:
        event = Event(
            type=type,
            source=source,
            ts=datetime.now(ZoneInfo("UTC")),
            payload=payload or {},
            path_to_file=path_to_file
        )
        
        for notifier in self.notifiers:
            try:
                notifier.notify(event)
            except Exception as e:
                print(f'Notifier failed: {e}')
    
    def _create_dashboard(self, name: str) -> None:
        # obtain the path to the location of the json where closed trades are stored in
        with open(self.engine_cfgs[name], 'r') as f:
            engine_cfg = json.load(f)
        path_to_trades = engine_cfg['eval_path'] + engine_cfg['name'] + '_trades.jsonl'

        # add fee model to registry and instatiate it; then instatiate corresp. trade blotter
        # and create a dashboard with relevant trading metrics
        if 'fees' in engine_cfg and os.path.exists(path_to_trades):
            fee_model = make_fee_model(engine_cfg['fees'])
            blotter = TradeBlotter(fee_model)

            path_to_dashboard = engine_cfg['eval_path'] + engine_cfg['name'] + '_dashboard.pdf'

            blotter.get_dashboard(path_to_trades, path_to_dashboard)

            return path_to_dashboard
        else:
            print(f'No fees model specified in {name} cfg file and/or\nNo file {path_to_trades} could be found')
            return None


    # ------------- Run engines ------------- #
    def run(self, max_restarts=3, reset_time=3600) -> None:
        """Runs all engines.

        This is the main method of the Supervisor class. It starts all engines, checks if engines crash and tries to restart them a specified amount of times. If chosen, it notifies about engine crashes, finished runs and once the supervisor has finished.

        Parameters
        ----------
        max_restarts : int, optional
            The maximum amount of tries to restart an engine after crashing; these are restart tries with an exponetially increasing wait between consecutive restarts, by default 3
        reset_time : int, optional
            The time elapsing before the restart count is being reset to zero; if an engine crashes (e.g. due to server being down) but then keeps running smoothly again, the restart count should be reset after some amount of time, by default 3600 (seconds)
        """        
        # start all engines
        for name, cfg in self.engine_cfgs.items():
            self.start_engine(name, cfg)
            
        print(f'===> All engines started successfully!')

        # setting up registries for engine crashes and restarts
        crash_count = {name: 0 for name in self.engine_cfgs}
        last_restart = {name: time.time() for name in self.engine_cfgs}
        restarts = {}

        try:
            while True:
                all_finished = True

                for name, p in list(self.processes.items()):
                    code = p.poll()
                    
                    # check whether some engines are still active; if so, set all_finished flag to False
                    if code is None:
                        all_finished = False
                        # reset crash count if enough time has elapsed since last crash
                        if time.time() - last_restart[name] > reset_time:
                            crash_count[name] = 0
                        continue

                    del self.processes[name]

                    # check whether engine finished normally; if so, notify
                    if code == 0:
                        print(f'Engine {name} finished normally')
                        self._emit(
                            type='engine_finished', 
                            source=name, 
                            path_to_file=self._create_dashboard(name)
                        )
                    # if engine crashed, adjust crash count, compute time to restart and register it
                    else:
                        print(f'{name} crashed (exit code: {code})')
                        all_finished = False
                        crash_count[name] += 1

                        if crash_count[name] <= max_restarts:
                            delay = min(300, 5 ** crash_count[name])
                            restarts[name] = time.time() + delay
                        # if max_restarts was exceeded, don't attempt another restart, but notify
                        else:
                            print(f"Engine {name} failed")
                            self._emit(
                                type='engine_failed', 
                                source=name, 
                                payload={'exit_code': code, 'crash_count': crash_count[name]}
                            )

                # if enough time has elapsed since crash, restart engine and delete entry in restart registry
                for name, ts in list(restarts.items()):
                    if time.time() >= ts:
                        self.start_engine(name, self.engine_cfgs[name])
                        last_restart[name] = time.time()
                        
                        del restarts[name]
                        # Optional: emit restart notification
                        # self._emit('engine_restarted', name, {'pid': self.processes[name].pid})

                # notify in case all engine have finished
                if all_finished and not restarts:
                    print('All engines finished. Shutting down...')
                    self._emit(
                        type='all_engines_finished',
                        source=self.name,
                        payload=crash_count
                    )
                    break

                time.sleep(2)
            
        except KeyboardInterrupt:
            print('KeyboardInterrupt! Shutting down...')
            self.shutdown()

    
