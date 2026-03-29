__all__ = ["root_agent", "run_pipeline"]


def __getattr__(name: str):
    if name in {"root_agent", "run_pipeline"}:
        from agents.root_agent import root_agent, run_pipeline

        return {"root_agent": root_agent, "run_pipeline": run_pipeline}[name]
    raise AttributeError(name)
