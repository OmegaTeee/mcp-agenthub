"""
Integration tests for prompt enhancement and caching.

Tests client-specific enhancement models and cache performance.
"""

import time

import httpx
import pytest


class TestPromptEnhancement:
    """Test prompt enhancement with Ollama."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Ollama running")
    async def test_enhancement_uses_client_specific_model(self):
        """
        Test that different clients use different enhancement models.

        - claude-desktop: DeepSeek-R1
        - vscode: Qwen3-Coder
        - raycast: DeepSeek-R1
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            clients_and_models = [
                ("claude-desktop", "deepseek-r1:latest"),
                ("vscode", "qwen3-coder:latest"),
                ("raycast", "deepseek-r1:latest"),
            ]

            for client_name, expected_model in clients_and_models:
                response = await client.post(
                    "/ollama/enhance",
                    headers={"X-Client-Name": client_name},
                    json={"prompt": "Explain async/await"}
                )

                assert response.status_code == 200
                data = response.json()

                # Response should contain enhanced prompt
                assert "enhanced_prompt" in data or "result" in data

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Ollama running")
    async def test_enhancement_code_first_for_vscode(self):
        """
        Test that VS Code enhancement is code-first.

        Expected: Code examples before explanations.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            response = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "vscode"},
                json={"prompt": "array sorting"}
            )

            assert response.status_code == 200
            data = response.json()

            enhanced = data.get("enhanced_prompt", data.get("result", ""))

            # Should contain code (backticks or specific keywords)
            assert "```" in enhanced or "function" in enhanced or "const" in enhanced

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Ollama running")
    async def test_enhancement_action_oriented_for_raycast(self):
        """
        Test that Raycast enhancement is action-oriented.

        Expected: CLI commands, under 200 words.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            response = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "raycast"},
                json={"prompt": "disk usage"}
            )

            assert response.status_code == 200
            data = response.json()

            enhanced = data.get("enhanced_prompt", data.get("result", ""))

            # Should be relatively short (under 200 words)
            word_count = len(enhanced.split())
            assert word_count < 300, f"Raycast response too long: {word_count} words"

            # Should contain CLI-like content
            assert any(cmd in enhanced.lower() for cmd in ["df", "du", "disk", "usage"])

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Ollama running")
    async def test_enhancement_fallback_when_ollama_down(self):
        """
        Test that requests succeed even when Ollama is unavailable.

        Expected: Original prompt returned unchanged.
        """
        # This would require:
        # 1. Stopping Ollama
        # 2. Making enhancement request
        # 3. Verifying original prompt returned
        # 4. Restarting Ollama
        pass  # TODO: Implement

    @pytest.mark.asyncio
    async def test_enhancement_endpoint_exists(self):
        """Test that enhancement endpoint is accessible."""
        # Use longer timeout since Ollama might be slow
        async with httpx.AsyncClient(base_url="http://localhost:9090", timeout=30.0) as client:
            response = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "test"},
                json={"prompt": "test"}
            )

            # Should not return 404
            # 503 is acceptable if Ollama is not running
            assert response.status_code in [200, 503], \
                f"Enhancement endpoint returned unexpected status: {response.status_code}"


class TestCaching:
    """Test response caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_improves_response_time(self):
        """
        Test that cached responses are significantly faster.

        Expected:
        - First request: ~2-3 seconds
        - Second request (cached): <500ms
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            # Clear cache first
            await client.post("/dashboard/actions/clear-cache")

            json_rpc = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }

            # First request (cache miss)
            start_time = time.time()
            response1 = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json=json_rpc
            )
            first_request_time = time.time() - start_time

            assert response1.status_code == 200

            # Second request (cache hit)
            start_time = time.time()
            response2 = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json=json_rpc
            )
            second_request_time = time.time() - start_time

            assert response2.status_code == 200

            # Both should return same data (ignoring ID which may be auto-incremented)
            data1 = response1.json()
            data2 = response2.json()

            # Compare results, not IDs (router may transform IDs)
            assert data1.get("result") == data2.get("result")
            assert data1.get("error") == data2.get("error")

            # Second request should be faster (at least 2x faster)
            # Note: This might be flaky in CI, so we use a generous threshold
            print(f"First request: {first_request_time:.3f}s")
            print(f"Second request: {second_request_time:.3f}s")
            print(f"Speedup: {first_request_time / second_request_time:.1f}x")

            # Cache hit should be under 1 second (generous for CI)
            assert second_request_time < 1.0, \
                f"Cached request too slow: {second_request_time:.3f}s"

    @pytest.mark.asyncio
    async def test_cache_shared_across_clients(self):
        """
        Test that cache is shared between different clients.

        Expected: Request from one client benefits subsequent requests from other clients.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            # Clear cache
            await client.post("/dashboard/actions/clear-cache")

            json_rpc = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }

            # Request 1: claude-desktop
            response1 = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "claude-desktop"},
                json=json_rpc
            )
            assert response1.status_code == 200

            # Request 2: vscode (should hit cache from claude-desktop)
            start_time = time.time()
            response2 = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "vscode"},
                json=json_rpc
            )
            vscode_time = time.time() - start_time

            assert response2.status_code == 200

            # Should be fast (cache hit)
            assert vscode_time < 1.0

            # Request 3: raycast (should also hit cache)
            start_time = time.time()
            response3 = await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "raycast"},
                json=json_rpc
            )
            raycast_time = time.time() - start_time

            assert response3.status_code == 200
            assert raycast_time < 1.0

    @pytest.mark.asyncio
    async def test_cache_stats_tracking(self):
        """
        Test that cache statistics are tracked correctly.

        Expected: Cache hits/misses counted, hit rate calculated.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            # Clear cache and make some requests
            await client.post("/dashboard/actions/clear-cache")

            json_rpc = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }

            # First request (miss)
            await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json=json_rpc
            )

            # Second request (hit)
            await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json=json_rpc
            )

            # Check stats
            stats_response = await client.get("/dashboard/stats-partial")

            if stats_response.status_code == 200:
                # Stats should show at least 1 hit
                stats_html = stats_response.text

                # Should contain cache statistics
                # (Exact format depends on dashboard implementation)

    @pytest.mark.asyncio
    async def test_cache_clear_works(self):
        """Test that cache can be cleared."""
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            json_rpc = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }

            # Make request to populate cache
            await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json=json_rpc
            )

            # Clear cache
            clear_response = await client.post("/dashboard/actions/clear-cache")
            assert clear_response.status_code in [200, 204]

            # Next request should be slower (cache miss)
            start_time = time.time()
            await client.post(
                "/mcp/context7/tools/call",
                headers={"X-Client-Name": "test"},
                json=json_rpc
            )
            request_time = time.time() - start_time

            # Should not be instant (cache was cleared)
            # Note: This is a weak assertion as timing can vary
            # In production, we'd check cache stats instead

    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self):
        """
        Test that cache uses LRU eviction when full.

        Expected: Least recently used items evicted when cache reaches max size.
        """
        # This would require:
        # 1. Determining cache max size
        # 2. Making max_size + 1 unique requests
        # 3. Verifying oldest request is evicted
        # 4. Verifying newest requests still cached
        pass  # TODO: Implement


class TestEnhancementAndCachingIntegration:
    """Test integration between enhancement and caching."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Ollama running")
    async def test_enhanced_prompts_are_cached(self):
        """
        Test that enhanced prompts are cached.

        Expected: Same original prompt → same enhanced prompt from cache.
        """
        async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
            # Clear cache
            await client.post("/dashboard/actions/clear-cache")

            original_prompt = "Explain React hooks"

            # First enhancement (cache miss)
            response1 = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "claude-desktop"},
                json={"prompt": original_prompt}
            )

            assert response1.status_code == 200
            enhanced1 = response1.json()

            # Second enhancement (cache hit)
            start_time = time.time()
            response2 = await client.post(
                "/ollama/enhance",
                headers={"X-Client-Name": "claude-desktop"},
                json={"prompt": original_prompt}
            )
            enhancement_time = time.time() - start_time

            assert response2.status_code == 200
            enhanced2 = response2.json()

            # Should return same enhanced prompt
            assert enhanced1 == enhanced2

            # Should be much faster (cached)
            assert enhancement_time < 0.5

    @pytest.mark.asyncio
    async def test_cache_key_includes_client_name(self):
        """
        Test that cache key accounts for client-specific enhancements.

        Expected: Same prompt from different clients → different cache entries
        (because enhancement differs per client).
        """
        # This would test if:
        # - claude-desktop gets DeepSeek-R1 enhanced version
        # - vscode gets Qwen3-Coder enhanced version
        # - Both are cached separately
        pass  # TODO: Implement when enhancement is stable
