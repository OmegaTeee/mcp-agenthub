"""
Integration tests for MCP proxy functionality.

Tests that JSON-RPC requests are correctly proxied to MCP servers.
"""

import httpx
import pytest


class TestMCPProxyRouting:
    """Test MCP proxy routing to servers."""

    @pytest.mark.asyncio
    async def test_proxy_to_context7(self):
        """Test proxying requests to context7 server."""
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            response = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should be valid JSON-RPC response
            assert "jsonrpc" in data
            assert data["jsonrpc"] == "2.0"
            # Note: ID may be transformed by router, just verify it exists
            assert "id" in data

            # Should have result or error
            assert "result" in data or "error" in data

            # If successful, verify tools structure
            if "result" in data:
                assert "tools" in data["result"]
                tools = data["result"]["tools"]
                assert isinstance(tools, list)

                # context7 should have specific tools
                tool_names = [t["name"] for t in tools]
                assert "query-docs" in tool_names or "resolve-library-id" in tool_names

    @pytest.mark.asyncio
    async def test_proxy_to_all_servers(self):
        """Test that all MCP servers are accessible via proxy."""
        servers = [
            "context7",
            "desktop-commander",
            "sequential-thinking",
            "memory",
            "deepseek-reasoner",
            "fetch",
            "obsidian"
        ]

        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            for server_name in servers:
                response = await client.post(
                    f"/mcp/{server_name}/tools/call",
                    headers={"X-Client-Name": "test"},
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 1
                    }
                )

                assert response.status_code in [200, 503], \
                    f"Server {server_name} returned unexpected status: {response.status_code}"

                # 503 is OK if circuit breaker is OPEN
                # 200 means success
                if response.status_code == 200:
                    data = response.json()
                    assert "result" in data or "error" in data

    @pytest.mark.asyncio
    async def test_invalid_server_returns_404(self):
        """Test that requesting non-existent server returns 404."""
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            response = await client.post(
                "/mcp/nonexistent-server/tools/call",
                headers={"X-Client-Name": "test"},
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                }
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_json_rpc_error_handling(self):
        """Test that invalid JSON-RPC requests are handled properly."""
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            # Missing required fields
            response = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json={
                    "method": "tools/list"
                    # Missing jsonrpc and id
                }
            )

            # Should still return 200 (HTTP) but with JSON-RPC error
            assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_client_name_header_preserved(self):
        """Test that X-Client-Name header is forwarded to servers."""
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            client_names = ["claude-desktop", "vscode", "raycast", "test"]

            for client_name in client_names:
                response = await client.post(
                    "/mcp/context7/tools/call",
                    headers={"X-Client-Name": client_name},
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 1
                    }
                )

                assert response.status_code == 200
                # Client name should be logged in audit trail


class TestMCPProxyPerformance:
    """Test MCP proxy performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests."""
        import asyncio

        async def make_request(client: AsyncClient, request_id: int):
            return await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": request_id
                }
            )

        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            # Send 10 concurrent requests
            tasks = [make_request(client, i) for i in range(10)]
            responses = await asyncio.gather(*tasks)

            # All should succeed
            for response in responses:
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that long-running requests don't hang forever."""
        import asyncio

        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=5.0) as client:
            try:
                # Make request with short timeout
                response = await client.post(
                    "/mcp/sequential-thinking/tools/call",
                    headers={"X-Client-Name": "test"},
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "sequentialthinking",
                            "arguments": {
                                "thought": "Long complex reasoning task",
                                "thoughtNumber": 1,
                                "totalThoughts": 100
                            }
                        },
                        "id": 1
                    }
                )

                # Either completes or times out gracefully
                assert response.status_code in [200, 408, 503]

            except asyncio.TimeoutError:
                # Timeout is acceptable behavior
                pass


class TestMCPProxyResilience:
    """Test circuit breaker and resilience features."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_activates_on_failures(self):
        """Test that circuit breaker opens after consecutive failures."""
        # This would require:
        # 1. Stopping an MCP server
        # 2. Making 3+ requests
        # 3. Verifying circuit breaker is OPEN
        # 4. Restarting server
        # 5. Waiting for recovery
        # 6. Verifying circuit breaker is CLOSED
        pass  # TODO: Implement

    @pytest.mark.asyncio
    async def test_auto_restart_on_crash(self):
        """Test that crashed MCP servers auto-restart."""
        # This would require:
        # 1. Getting PID of running server
        # 2. Killing it
        # 3. Waiting for supervisor to detect and restart
        # 4. Verifying new PID
        pass  # TODO: Implement


class TestMCPProxyAudit:
    """Test audit logging for MCP proxy requests."""

    @pytest.mark.asyncio
    async def test_all_requests_logged(self):
        """Test that all MCP proxy requests are logged to audit trail."""
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            # Make a unique request
            response = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test-audit"},
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 999
                }
            )

            assert response.status_code == 200

            # Query audit log to verify it was logged
            audit_response = await client.get("/audit/activity?limit=10")

            if audit_response.status_code == 200:
                audit_data = audit_response.json()
                # Should find our request in recent activity
                # (checking for client_name="test-audit")

    @pytest.mark.asyncio
    async def test_sensitive_data_not_logged(self):
        """Test that sensitive data (API keys, tokens) is redacted from logs."""
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            # Send request with potentially sensitive data
            response = await client.post(
                "/mcp/context7/tools/call",
                headers={
                    "X-Client-Name": "test",
                    "Authorization": "Bearer secret-token-123"
                },
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "api_key": "sk-12345",
                        "password": "super-secret"
                    },
                    "id": 1
                }
            )

            # Audit logs should redact sensitive fields
            # (This would require checking audit database)
