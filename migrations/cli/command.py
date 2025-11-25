class CLICommand:
    """
    Abstract base class for CLI commands.
    """

    def execute(self):
        raise NotImplementedError("Subclasses should implement this method.")
