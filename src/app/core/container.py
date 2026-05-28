"""Simple dependency container for application wiring."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.commands.registry import CommandRegistry
from app.config.settings import Settings
from app.infrastructure.ffmpeg.runner import FfmpegRunner
from app.infrastructure.hydrogram.client_factory import TelegramClientFactory
from app.infrastructure.hydrogram.message_edit_gateway import MessageEditGateway
from app.infrastructure.hydrogram.reaction_gateway import ReactionGateway
from app.infrastructure.hydrogram.sticker_set_gateway import StickerSetGateway
from app.infrastructure.media.sticker_processor import StickerProcessor
from app.infrastructure.media.tgs_to_gif_converter import TgsToGifConverter
from app.infrastructure.repositories.reaction_state_repository import ReactionStateRepository
from app.infrastructure.shell.awk_runner import AwkRunner
from app.infrastructure.storage.json_state_store import JsonStateStore
from app.infrastructure.storage.temp_file_manager import TempFileManager


@dataclass
class Container:
    """Holds shared services for handlers and plugins."""

    settings: Settings
    command_registry: CommandRegistry = field(default_factory=CommandRegistry)
    state_store: JsonStateStore = field(init=False)
    temp_files: TempFileManager = field(init=False)
    ffmpeg: FfmpegRunner = field(init=False)
    sticker_processor: StickerProcessor = field(init=False)
    client_factory: TelegramClientFactory = field(init=False)
    reaction_repository: ReactionStateRepository = field(init=False)
    reaction_gateway: ReactionGateway = field(init=False)
    sticker_set_gateway: StickerSetGateway = field(init=False)
    tgs_to_gif: TgsToGifConverter = field(init=False)
    message_edit_gateway: MessageEditGateway = field(init=False)
    awk_runner: AwkRunner = field(init=False)

    def __post_init__(self) -> None:
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings.temp_dir.mkdir(parents=True, exist_ok=True)
        self.state_store = JsonStateStore(self.settings.data_dir / "state.json")
        self.temp_files = TempFileManager(self.settings.temp_dir)
        self.ffmpeg = FfmpegRunner(
            binary=self.settings.ffmpeg_path,
            timeout_seconds=self.settings.ffmpeg_timeout_seconds,
        )
        self.sticker_processor = StickerProcessor(
            max_dimension=self.settings.sticker_max_dimension,
        )
        self.client_factory = TelegramClientFactory(self.settings)
        self.reaction_repository = ReactionStateRepository(self.state_store)
        self.reaction_gateway = ReactionGateway(
            cooldown_seconds=self.settings.reaction_cooldown_seconds,
            max_retries=self.settings.reaction_max_retries,
            fallback_emojis=self.settings.fallback_emoji_list,
        )
        self.sticker_set_gateway = StickerSetGateway()
        self.tgs_to_gif = TgsToGifConverter(
            max_dimension=self.settings.gif_max_width,
            fps=self.settings.gif_fps,
        )
        self.message_edit_gateway = MessageEditGateway(
            delay_seconds=self.settings.stream_edit_delay_seconds,
            max_retries=self.settings.stream_edit_max_retries,
        )
        self.awk_runner = AwkRunner(
            binary=self.settings.awk_path,
            timeout_seconds=self.settings.awk_timeout_seconds,
        )
