"""nanobot-feishu-tools: Feishu/Lark tools plugin for nanobot."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from nanobot.agent.tools.registry import ToolRegistry
    from nanobot.config.schema import Config

# Skills bundled with this package
_SKILLS_DIR = Path(__file__).parent / "skills"


def _install_skills(config: Config) -> None:
    """Copy bundled SKILL.md files into the nanobot workspace skills directory."""
    try:
        workspace = Path(config.agents.defaults.workspace).expanduser()
    except (AttributeError, TypeError):
        return

    dst_root = workspace / "skills"
    if not dst_root.exists():
        return

    if not _SKILLS_DIR.exists():
        return

    for skill_dir in _SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        src_skill = skill_dir / "SKILL.md"
        if not src_skill.exists():
            continue

        dst_skill_dir = dst_root / skill_dir.name
        dst_skill_file = dst_skill_dir / "SKILL.md"

        # Only copy if missing or source is newer
        if dst_skill_file.exists() and dst_skill_file.stat().st_mtime >= src_skill.stat().st_mtime:
            continue

        dst_skill_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_skill, dst_skill_file)
        logger.debug("feishu-tools: Installed skill '{}'", skill_dir.name)


def register_tools(registry: ToolRegistry, config: Config) -> None:
    """Entry point called by nanobot's tool plugin discovery."""
    from nanobot_feishu_tools._config import resolve_settings
    from nanobot_feishu_tools._client import get_client

    # Install skills into workspace (regardless of credentials)
    try:
        _install_skills(config)
    except Exception as e:
        logger.debug("feishu-tools: Could not install skills: {}", e)

    settings = resolve_settings(config)
    if not settings:
        logger.debug("feishu-tools: No Feishu credentials found, skipping")
        return

    client = get_client(settings)

    from nanobot_feishu_tools.doc.tool import FeishuDocTool
    from nanobot_feishu_tools.wiki.tool import FeishuWikiTool
    from nanobot_feishu_tools.bitable.tools import get_bitable_tools
    from nanobot_feishu_tools.task.tools import get_task_tools
    from nanobot_feishu_tools.perm.tool import FeishuPermTool
    from nanobot_feishu_tools.im.tool import FeishuImTool

    registry.register(FeishuDocTool(client))
    registry.register(FeishuWikiTool(client))
    registry.register(FeishuPermTool(client))
    registry.register(FeishuImTool(client))

    for tool in get_bitable_tools(client):
        registry.register(tool)

    for tool in get_task_tools(client):
        registry.register(tool)

    logger.info("feishu-tools: Registered doc, wiki, bitable, task, perm, im tools")
