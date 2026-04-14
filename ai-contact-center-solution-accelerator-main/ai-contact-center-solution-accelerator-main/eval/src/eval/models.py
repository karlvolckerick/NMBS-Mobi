from dataclasses import dataclass, field


@dataclass
class FunctionCallExpectation:
    """A function call expectation from the scenario definition."""

    plugin: str
    function_name: str

    def matches(self, other: "FunctionCallExpectation") -> bool:
        return self.plugin == other.plugin and self.function_name == other.function_name


@dataclass
class FunctionCallRecord:
    """A function call captured from the WebSocket during a conversation."""

    agent: str
    plugin: str
    function: str
    arguments: str = ""


@dataclass
class FunctionResultRecord:
    """A function result captured from the WebSocket during a conversation."""

    agent: str
    plugin: str
    function: str
    result: str = ""


@dataclass
class TranscriptMessage:
    """A single message in the conversation transcript.

    Uses 'content' instead of 'text' to match Azure AI Evaluation SDK format.
    """

    role: str  # "user", "assistant", or agent name
    content: str
    timestamp: float | None = None


@dataclass
class ScenarioResult:
    """Result of running a single conversation scenario."""

    scenario_name: str
    transcript: list[TranscriptMessage] = field(default_factory=list)
    function_calls: list[FunctionCallRecord] = field(default_factory=list)
    function_results: list[FunctionResultRecord] = field(default_factory=list)
    agent_switches: list[str] = field(default_factory=list)
    final_agent: str | None = None
    turns: int = 0
    error: str = ""
