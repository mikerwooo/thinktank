const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const { existsSync, mkdirSync, writeFileSync, rmSync, readFileSync, unlinkSync } = require('node:fs');
const { join } = require('node:path');
const { tmpdir } = require('node:os');
const { execSync } = require('node:child_process');

const PROVIDERS_DIR = join(__dirname, '..', '..', 'providers');

function toUnixPath(p) {
    return p.replace(/\\/g, '/').replace(/^([A-Za-z]):/, (_, d) => `/${d.toLowerCase()}`);
}

function sourceAndRun(providerScript, bashCode) {
    const unixPath = toUnixPath(providerScript);
    const tmpFile = join(tmpdir(), `loki-provider-test-${Date.now()}-${Math.random().toString(36).slice(2)}.sh`);
    const script = `#!/usr/bin/env bash\nset +e\nsource "${unixPath}" 2>/dev/null\n${bashCode}\n`;
    writeFileSync(tmpFile, script, { mode: 0o755 });
    try {
        return execSync(`bash "${toUnixPath(tmpFile)}"`, {
            encoding: 'utf8',
            timeout: 5000,
            env: { ...process.env, PATH: process.env.PATH }
        }).trim();
    } catch (err) {
        return err.stdout ? err.stdout.trim() : '';
    } finally {
        try { unlinkSync(tmpFile); } catch { /* ignore */ }
    }
}

describe('Provider Loader', () => {
    const loaderPath = join(PROVIDERS_DIR, 'loader.sh');

    it('loader.sh exists and has valid bash syntax', () => {
        assert.ok(existsSync(loaderPath), 'loader.sh should exist');
        assert.doesNotThrow(() => {
            execSync(`bash -n "${loaderPath}"`, { encoding: 'utf8', timeout: 5000 });
        }, 'loader.sh should have valid bash syntax');
    });

    it('defines SUPPORTED_PROVIDERS array', () => {
        const output = sourceAndRun(loaderPath, 'echo "${SUPPORTED_PROVIDERS[@]}"');
        assert.ok(output.includes('claude'), 'SUPPORTED_PROVIDERS should include claude');
        assert.ok(output.includes('codex'), 'SUPPORTED_PROVIDERS should include codex');
        assert.ok(output.includes('gemini'), 'SUPPORTED_PROVIDERS should include gemini');
    });

    it('defines DEFAULT_PROVIDER as claude', () => {
        const output = sourceAndRun(loaderPath, 'echo "$DEFAULT_PROVIDER"');
        assert.equal(output, 'claude');
    });

    it('validate_provider accepts valid provider names', () => {
        const result = sourceAndRun(loaderPath, 'validate_provider claude; echo $?');
        assert.equal(result, '0', 'validate_provider should accept claude');
    });

    it('validate_provider rejects invalid provider names', () => {
        const result = sourceAndRun(loaderPath, 'validate_provider invalid_provider 2>/dev/null; echo $?');
        assert.notEqual(result, '0', 'validate_provider should reject invalid provider names');
    });

    it('validate_provider rejects path traversal attempts', () => {
        const result = sourceAndRun(loaderPath, 'validate_provider "../etc/passwd" 2>/dev/null; echo $?');
        assert.notEqual(result, '0', 'validate_provider should reject path traversal');
    });
});

describe('Provider Config Files', () => {
    const providers = ['claude', 'codex', 'gemini', 'cline', 'aider'];

    for (const provider of providers) {
        const providerPath = join(PROVIDERS_DIR, `${provider}.sh`);

        it(`${provider}.sh exists and has valid bash syntax`, () => {
            assert.ok(existsSync(providerPath), `${provider}.sh should exist`);
            assert.doesNotThrow(() => {
                execSync(`bash -n "${providerPath}"`, { encoding: 'utf8', timeout: 5000 });
            }, `${provider}.sh should have valid bash syntax`);
        });

        it(`${provider}.sh exports PROVIDER_NAME`, () => {
            const output = sourceAndRun(providerPath, 'echo "$PROVIDER_NAME"');
            assert.equal(output, provider, `PROVIDER_NAME should be "${provider}"`);
        });

        it(`${provider}.sh exports PROVIDER_CLI`, () => {
            const output = sourceAndRun(providerPath, 'echo "$PROVIDER_CLI"');
            assert.ok(output.length > 0, `PROVIDER_CLI should be set for ${provider}`);
        });

        it(`${provider}.sh exports PROVIDER_AUTONOMOUS_FLAG`, () => {
            const output = sourceAndRun(providerPath, 'echo "$PROVIDER_AUTONOMOUS_FLAG"');
            assert.ok(output.length > 0, `PROVIDER_AUTONOMOUS_FLAG should be set for ${provider}`);
        });

        it(`${provider}.sh exports capability flags`, () => {
            const hasSubagents = sourceAndRun(providerPath, 'echo "$PROVIDER_HAS_SUBAGENTS"');
            const hasParallel = sourceAndRun(providerPath, 'echo "$PROVIDER_HAS_PARALLEL"');
            const hasTaskTool = sourceAndRun(providerPath, 'echo "$PROVIDER_HAS_TASK_TOOL"');
            const hasMcp = sourceAndRun(providerPath, 'echo "$PROVIDER_HAS_MCP"');

            for (const [flag, value] of [['HAS_SUBAGENTS', hasSubagents], ['HAS_PARALLEL', hasParallel], ['HAS_TASK_TOOL', hasTaskTool], ['HAS_MCP', hasMcp]]) {
                assert.ok(
                    value === 'true' || value === 'false',
                    `PROVIDER_${flag} should be true or false for ${provider}, got "${value}"`
                );
            }
        });

        it(`${provider}.sh exports PROVIDER_DEGRADED flag`, () => {
            const output = sourceAndRun(providerPath, 'echo "$PROVIDER_DEGRADED"');
            assert.ok(
                output === 'true' || output === 'false',
                `PROVIDER_DEGRADED should be true or false for ${provider}, got "${output}"`
            );
        });
    }

    it('claude.sh has full capabilities', () => {
        const claudePath = join(PROVIDERS_DIR, 'claude.sh');
        const subagents = sourceAndRun(claudePath, 'echo "$PROVIDER_HAS_SUBAGENTS"');
        const parallel = sourceAndRun(claudePath, 'echo "$PROVIDER_HAS_PARALLEL"');
        const taskTool = sourceAndRun(claudePath, 'echo "$PROVIDER_HAS_TASK_TOOL"');
        const mcp = sourceAndRun(claudePath, 'echo "$PROVIDER_HAS_MCP"');
        const degraded = sourceAndRun(claudePath, 'echo "$PROVIDER_DEGRADED"');

        assert.equal(subagents, 'true', 'Claude should have subagents');
        assert.equal(parallel, 'true', 'Claude should have parallel');
        assert.equal(taskTool, 'true', 'Claude should have Task tool');
        assert.equal(mcp, 'true', 'Claude should have MCP');
        assert.equal(degraded, 'false', 'Claude should not be degraded');
    });

    it('codex.sh is degraded without parallel or subagents', () => {
        const codexPath = join(PROVIDERS_DIR, 'codex.sh');
        const degraded = sourceAndRun(codexPath, 'echo "$PROVIDER_DEGRADED"');
        const parallel = sourceAndRun(codexPath, 'echo "$PROVIDER_HAS_PARALLEL"');
        const subagents = sourceAndRun(codexPath, 'echo "$PROVIDER_HAS_SUBAGENTS"');

        assert.equal(degraded, 'true', 'Codex should be degraded');
        assert.equal(parallel, 'false', 'Codex should not have parallel');
        assert.equal(subagents, 'false', 'Codex should not have subagents');
    });

    it('gemini.sh is degraded without MCP', () => {
        const geminiPath = join(PROVIDERS_DIR, 'gemini.sh');
        const degraded = sourceAndRun(geminiPath, 'echo "$PROVIDER_DEGRADED"');
        const mcp = sourceAndRun(geminiPath, 'echo "$PROVIDER_HAS_MCP"');

        assert.equal(degraded, 'true', 'Gemini should be degraded');
        assert.equal(mcp, 'false', 'Gemini should not have MCP');
    });
});
