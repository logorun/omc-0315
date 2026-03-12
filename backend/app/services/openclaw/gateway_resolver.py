"""DB-backed gateway resolution helpers.

This module is the narrow boundary between Mission Control's DB models and the
DB-free OpenClaw gateway client/provisioning layers.

Goals:
- Centralize "board -> gateway row" resolution and defensive org checks.
- Centralize construction of `GatewayConfig` objects used by gateway RPC calls.
- Keep call-sites thin and avoid re-implementing the same validation rules.
"""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.models.boards import Board
from app.models.gateways import Gateway
from app.services.openclaw.gateway_rpc import GatewayConfig as GatewayClientConfig

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


# Docker host networking constants
DOCKER_HOST_INTERNAL = "host.docker.internal"
DOCKER_BRIDGE_LINUX = "172.17.0.1"


def _resolve_docker_host_url(url: str) -> str:
    """Resolve host.docker.internal to a working address on Linux.
    
    On Docker Desktop (macOS/Windows), host.docker.internal works out of the box.
    On Linux, it's not available and needs to be replaced with the Docker bridge IP.
    """
    if DOCKER_HOST_INTERNAL not in url:
        return url
    
    # Only apply this fix on Linux systems
    if platform.system().lower() != "linux":
        return url
    
    # Replace host.docker.internal with Docker bridge IP
    resolved_url = url.replace(DOCKER_HOST_INTERNAL, DOCKER_BRIDGE_LINUX)
    return resolved_url


def gateway_client_config(gateway: Gateway) -> GatewayClientConfig:
    """Build a gateway RPC config from a Gateway model, requiring a URL."""
    url = (gateway.url or "").strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Gateway url is required",
        )
    # Resolve host.docker.internal for Linux Docker compatibility
    url = _resolve_docker_host_url(url)
    token = (gateway.token or "").strip() or None
    return GatewayClientConfig(
        url=url,
        token=token,
        allow_insecure_tls=gateway.allow_insecure_tls,
        disable_device_pairing=gateway.disable_device_pairing,
    )


def optional_gateway_client_config(gateway: Gateway | None) -> GatewayClientConfig | None:
    """Build a gateway RPC config when the gateway is configured; otherwise return None."""
    if gateway is None:
        return None
    url = (gateway.url or "").strip()
    if not url:
        return None
    url = _resolve_docker_host_url(url)
    token = (gateway.token or "").strip() or None
    return GatewayClientConfig(
        url=url,
        token=token,
        allow_insecure_tls=gateway.allow_insecure_tls,
        disable_device_pairing=gateway.disable_device_pairing,
    )


def require_gateway_workspace_root(gateway: Gateway) -> str:
    """Return a gateway workspace_root string, requiring it to be configured."""
    workspace_root = (gateway.workspace_root or "").strip()
    if not workspace_root:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Gateway workspace_root is required",
        )
    return workspace_root


async def get_gateway_for_board(
    session: AsyncSession,
    board: Board,
) -> Gateway | None:
    """Return the gateway for a board when present and valid; otherwise return None."""
    if board.gateway_id is None:
        return None
    gateway = await Gateway.objects.by_id(board.gateway_id).first(session)
    if gateway is None:
        return None
    # Defensive guard: boards and gateways are tenant-scoped; reject cross-org mismatches.
    if gateway.organization_id != board.organization_id:
        return None
    return gateway


async def require_gateway_for_board(
    session: AsyncSession,
    board: Board,
    *,
    require_workspace_root: bool = False,
) -> Gateway:
    """Return a board's gateway or raise a 422 with a stable error message."""
    if board.gateway_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Board gateway_id is required",
        )
    gateway = await get_gateway_for_board(session, board)
    if gateway is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Board gateway_id is invalid",
        )
    if require_workspace_root:
        require_gateway_workspace_root(gateway)
    return gateway
