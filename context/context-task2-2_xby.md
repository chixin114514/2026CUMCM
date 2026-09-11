# Codex conversation

## User

请修正当前问题二实现，其他模型结构、参数、数值方法和输出格式全部保持不变。唯一需要修改的是烘房边界条件：不要在 1800 s 后把 `T_air` 和 `C_air` 固定为 1800 s 的末值。`附件1.xlsx` 实际提供了直到 14400 s 的烘房温度和水分浓度数据，而问题二只计算到 10800 s，因此整个 `0–10800 s` 都应直接使用附件1中的真实数据，并继续采用分段线性插值得到任意时刻的 `T_air(t)` 和 `C_air(t)`。删除或修改类似 `selected = selected[selected["时间"] <= 1800]` 这种截断逻辑，然后重新运行完整 3 h 求解，重新生成 `result2.xlsx`、`task2_all_results.csv`、表3和表4，并重新执行原有数值验证。完成后用中文 commit message 提交本次修复，并报告修复后的关键结果和 commit hash。

## Assistant

状态：将只修正附件1边界数据的截断逻辑，保持 PDE、动态物性、Picard、网格、时间步和文件格式不变。先用现有实现复现“10800 s 仍返回 1800 s 边界值”，随后交给 `luna-worker` 修改、完整重算并提交。这里使用 `systematic-debugging` 定位该单点错误，并按 spreadsheet 交付规则重新核验 XLSX。

## Activity

    $ /bin/zsh -lc "sed -n '1,360p' /Users/jiaqiaosu/.agents/skills/systematic-debugging/SKILL.md && sed -n '1,360p' /Users/jiaqiaosu/.agents/skills/test-driven-development/SKILL.md && sed -n '1,320p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/SKILL.md"
    status: Completed · exit 0
      ---
      name: systematic-debugging
      description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
      ---
      
      # Systematic Debugging
      
      ## Overview
      
      Random fixes waste time and create new bugs. Quick patches mask underlying issues.
      
      **Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.
      
      **Violating the letter of this process is violating the spirit of debugging.**
      
      ## The Iron Law
      
      ```
      NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
      ```
      
      If you haven't completed Phase 1, you cannot propose fixes.
      
      ## When to Use
      
      Use for ANY technical issue:
      - Test failures
      - Bugs in production
      - Unexpected behavior
      - Performance problems
      - Build failures
      - Integration issues
      
      **Use this ESPECIALLY when:**
      - Under time pressure (emergencies make guessing tempting)
      - "Just one quick fix" seems obvious
      - You've already tried multiple fixes
      - Previous fix didn't work
      - You don't fully understand the issue
      
      **Don't skip when:**
      - Issue seems simple (simple bugs have root causes too)
      - You're in a hurry (rushing guarantees rework)
      - Manager wants it fixed NOW (systematic is faster than thrashing)
      
      ## The Four Phases
      
      You MUST complete each phase before proceeding to the next.
      
      ### Phase 1: Root Cause Investigation
      
      **BEFORE attempting ANY fix:**
      
      1. **Read Error Messages Carefully**
         - Don't skip past errors or warnings
         - They often contain the exact solution
         - Read stack traces completely
         - Note line numbers, file paths, error codes
      
      2. **Reproduce Consistently**
         - Can you trigger it reliably?
         - What are the exact steps?
         - Does it happen every time?
         - If not reproducible → gather more data, don't guess
      
      3. **Check Recent Changes**
         - What changed that could cause this?
         - Git diff, recent commits
         - New dependencies, config changes
         - Environmental differences
      
      4. **Gather Evidence in Multi-Component Systems**
      
         **WHEN system has multiple components (CI → build → signing, API → service → database):**
      
         **BEFORE proposing fixes, add diagnostic instrumentation:**
         ```
         For EACH component boundary:
           - Log what data enters component
           - Log what data exits component
           - Verify environment/config propagation
           - Check state at each layer
      
         Run once to gather evidence showing WHERE it breaks
         THEN analyze evidence to identify failing component
         THEN investigate that specific component
         ```
      
         **Example (multi-layer system):**
         ```bash
         # Layer 1: Workflow
         echo "=== Secrets available in workflow: ==="
         echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"
      
         # Layer 2: Build script
         echo "=== Env vars in build script: ==="
         env | grep IDENTITY || echo "IDENTITY not in environment"
      
         # Layer 3: Signing script
         echo "=== Keychain state: ==="
         security list-keychains
         security find-identity -v
      
         # Layer 4: Actual signing
         codesign --sign "$IDENTITY" --verbose=4 "$APP"
         ```
      
         **This reveals:** Which layer fails (secrets → workflow ✓, workflow → build ✗)
      
      5. **Trace Data Flow**
      
         **WHEN error is deep in call stack:**
      
         See `root-cause-tracing.md` in this directory for the complete backward tracing technique.
      
         **Quick version:**
         - Where does bad value originate?
         - What called this with bad value?
         - Keep tracing up until you find the source
         - Fix at source, not at symptom
      
      ### Phase 2: Pattern Analysis
      
      **Find the pattern before fixing:**
      
      1. **Find Working Examples**
         - Locate similar working code in same codebase
         - What works that's similar to what's broken?
      
      2. **Compare Against References**
         - If implementing pattern, read reference implementation COMPLETELY
         - Don't skim - read every line
         - Understand the pattern fully before applying
      
      3. **Identify Differences**
         - What's different between working and broken?
         - List every difference, however small
         - Don't assume "that can't matter"
      
      4. **Understand Dependencies**
         - What other components does this need?
         - What settings, config, environment?
         - What assumptions does it make?
      
      ### Phase 3: Hypothesis and Testing
      
      **Scientific method:**
      
      1. **Form Single Hypothesis**
         - State clearly: "I think X is the root cause because Y"
         - Write it down
         - Be specific, not vague
      
      2. **Test Minimally**
         - Make the SMALLEST possible change to test hypothesis
         - One variable at a time
         - Don't fix multiple things at once
      
      3. **Verify Before Continuing**
         - Did it work? Yes → Phase 4
         - Didn't work? Form NEW hypothesis
         - DON'T add more fixes on top
      
      4. **When You Don't Know**
         - Say "I don't understand X"
         - Don't pretend to know
         - Ask for help
         - Research more
      
      ### Phase 4: Implementation
      
      **Fix the root cause, not the symptom:**
      
      1. **Create Failing Test Case**
         - Simplest possible reproduction
         - Automated test if possible
         - One-off test script if no framework
         - MUST have before fixing
         - Use the `superpowers:test-driven-development` skill for writing proper failing tests
      
      2. **Implement Single Fix**
         - Address the root cause identified
         - ONE change at a time
         - No "while I'm here" improvements
         - No bundled refactoring
      
      3. **Verify Fix**
         - Test passes now?
         - No other tests broken?
         - Issue actually resolved?
      
      4. **If Fix Doesn't Work**
         - STOP
         - Count: How many fixes have you tried?
         - If < 3: Return to Phase 1, re-analyze with new information
         - **If ≥ 3: STOP and question the architecture (step 5 below)**
         - DON'T attempt Fix #4 without architectural discussion
      
      5. **If 3+ Fixes Failed: Question Architecture**
      
         **Pattern indicating architectural problem:**
         - Each fix reveals new shared state/coupling/problem in different place
         - Fixes require "massive refactoring" to implement
         - Each fix creates new symptoms elsewhere
      
         **STOP and question fundamentals:**
         - Is this pattern fundamentally sound?
         - Are we "sticking with it through sheer inertia"?
         - Should we refactor architecture vs. continue fixing symptoms?
      
         **Discuss with your human partner before attempting more fixes**
      
         This is NOT a failed hypothesis - this is a wrong architecture.
      
      ## Red Flags - STOP and Follow Process
      
      If you catch yourself thinking:
      - "Quick fix for now, investigate later"
      - "Just try changing X and see if it works"
      - "Add multiple changes, run tests"
      - "Skip the test, I'll manually verify"
      - "It's probably X, let me fix that"
      - "I don't fully understand but this might work"
      - "Pattern says X but I'll adapt it differently"
      - "Here are the main problems: [lists fixes without investigation]"
      - Proposing solutions before tracing data flow
      - **"One more fix attempt" (when already tried 2+)**
      - **Each fix reveals new problem in different place**
      
      **ALL of these mean: STOP. Return to Phase 1.**
      
      **If 3+ fixes failed:** Question the architecture (see Phase 4.5)
      
      ## your human partner's Signals You're Doing It Wrong
      
      **Watch for these redirections:**
      - "Is that not happening?" - You assumed without verifying
      - "Will it show us...?" - You should have added evidence gathering
      - "Stop guessing" - You're proposing fixes without understanding
      - "Ultrathink this" - Question fundamentals, not just symptoms
      - "We're stuck?" (frustrated) - Your approach isn't working
      
      **When you see these:** STOP. Return to Phase 1.
      
      ## Common Rationalizations
      
      | Excuse | Reality |
      |--------|---------|
      | "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
      | "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
      | "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
      | "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
      | "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
      | "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
      | "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
      | "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question pattern, don't fix again. |
      
      ## Quick Reference
      
      | Phase | Key Activities | Success Criteria |
      |-------|---------------|------------------|
      | **1. Root Cause** | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
      | **2. Pattern** | Find working examples, compare | Identify differences |
      | **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
      | **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |
      
      ## When Process Reveals "No Root Cause"
      
      If systematic investigation reveals issue is truly environmental, timing-dependent, or external:
      
      1. You've completed the process
      2. Document what you investigated
      3. Implement appropriate handling (retry, timeout, error message)
      4. Add monitoring/logging for future investigation
      
      **But:** 95% of "no root cause" cases are incomplete investigation.
      
      ## Supporting Techniques
      
      These techniques are part of systematic debugging and available in this directory:
      
      - **`root-cause-tracing.md`** - Trace bugs backward through call stack to find original trigger
      - **`defense-in-depth.md`** - Add validation at multiple layers after finding root cause
      - **`condition-based-waiting.md`** - Replace arbitrary timeouts with condition polling
      
      **Related skills:**
      - **superpowers:test-driven-development** - For creating failing test case (Phase 4, Step 1)
      - **superpowers:verification-before-completion** - Verify fix worked before claiming success
      
      ## Real-World Impact
      
      From debugging sessions:
      - Systematic approach: 15-30 minutes to fix
      - Random fixes approach: 2-3 hours of thrashing
      - First-time fix rate: 95% vs 40%
      - New bugs introduced: Near zero vs common
      ---
      name: test-driven-development
      description: Use when implementing any feature or bugfix, before writing implementation code
      ---
      
      # Test-Driven Development (TDD)
      
      ## Overview
      
      Write the test first. Watch it fail. Write minimal code to pass.
      
      **Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.
      
      **Violating the letter of the rules is violating the spirit of the rules.**
      
      ## When to Use
      
      **Always:**
      - New features
      - Bug fixes
      - Refactoring
      - Behavior changes
      
      **Exceptions (ask your human partner):**
      - Throwaway prototypes
      - Generated code
      - Configuration files
      
      Thinking "skip TDD just this once"? Stop. That's rationalization.
      
      ## The Iron Law
      
      ```
      NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
      ```
      
      Write code before the test? Delete it. Start over.
      
      **No exceptions:**
      - Don't keep it as "reference"
      - Don't "adapt" it while writing tests
      - Don't look at it
      - Delete means delete
      
      Implement fresh from tests. Period.
      
      ## Red-Green-Refactor
      
      ```dot
      digraph tdd_cycle {
          rankdir=LR;
          red [label="RED\nWrite failing test", shape=box, style=filled, fillcolor="#ffcccc"];
          verify_red [label="Verify fails\ncorrectly", shape=diamond];
          green [label="GREEN\nMinimal code", shape=box, style=filled, fillcolor="#ccffcc"];
          verify_green [label="Verify passes\nAll green", shape=diamond];
          refactor [label="REFACTOR\nClean up", shape=box, style=filled, fillcolor="#ccccff"];
          next [label="Next", shape=ellipse];
      
          red -> verify_red;
          verify_red -> green [label="yes"];
          verify_red -> red [label="wrong\nfailure"];
          green -> verify_green;
          verify_green -> refactor [label="yes"];
          verify_green -> green [label="no"];
          refactor -> verify_green [label="stay\ngreen"];
          verify_green -> next;
          next -> red;
      }
      ```
      
      ### RED - Write Failing Test
      
      Write one minimal test showing what should happen.
      
      <Good>
      ```typescript
      test('retries failed operations 3 times', async () => {
        let attempts = 0;
        const operation = () => {
          attempts++;
          if (attempts < 3) throw new Error('fail');
          return 'success';
        };
      
        const result = await retryOperation(operation);
      
        expect(result).toBe('success');
        expect(attempts).toBe(3);
      });
      ```
      Clear name, tests real behavior, one thing
      </Good>
      
      <Bad>
      ```typescript
      test('retry works', async () => {
        const mock = jest.fn()
          .mockRejectedValueOnce(new Error())
          .mockRejectedValueOnce(new Error())
          .mockResolvedValueOnce('success');
        await retryOperation(mock);
        expect(mock).toHaveBeenCalledTimes(3);
      });
      ```
      Vague name, tests mock not code
      </Bad>
      
      **Requirements:**
      - One behavior
      - Clear name
      - Real code (no mocks unless unavoidable)
      
      ### Verify RED - Watch It Fail
      
      **MANDATORY. Never skip.**
      
      ```bash
      npm test path/to/test.test.ts
      ```
      
      Confirm:
      - Test fails (not errors)
      - Failure message is expected
      - Fails because feature missing (not typos)
      
      **Test passes?** You're testing existing behavior. Fix test.
      
      **Test errors?** Fix error, re-run until it fails correctly.
      
      ### GREEN - Minimal Code
      
      Write simplest code to pass the test.
      
      <Good>
      ```typescript
      async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
        for (let i = 0; i < 3; i++) {
          try {
            return await fn();
          } catch (e) {
            if (i === 2) throw e;
          }
        }
        throw new Error('unreachable');
      }
      ```
      Just enough to pass
      </Good>
      
      <Bad>
      ```typescript
      async function retryOperation<T>(
        fn: () => Promise<T>,
        options?: {
          maxRetries?: number;
          backoff?: 'linear' | 'exponential';
          onRetry?: (attempt: number) => void;
        }
      ): Promise<T> {
        // YAGNI
      }
      ```
      Over-engineered
      </Bad>
      
      Don't add features, refactor other code, or "improve" beyond the test.
      
      ### Verify GREEN - Watch It Pass
      
      **MANDATORY.**
      
      ```bash
      npm test path/to/test.test.ts
      ```
      
      Confirm:
      - Test passes
      - Other tests still pass
      - Output pristine (no errors, warnings)
      
      **Test fails?** Fix code, not test.
      
      **Other tests fail?** Fix now.
      
      ### REFACTOR - Clean Up
      
      After green only:
      - Remove duplication
      - Improve names
      - Extract helpers
      
      Keep tests green. Don't add behavior.
      
      ### Repeat
      
      Next failing test for next feature.
      
      ## Good Tests
      
      | Quality | Good | Bad |
      |---------|------|-----|
      | **Minimal** | One thing. "and" in name? Split it. | `test('validates email and domain and whitespace')` |
      | **Clear** | Name describes behavior | `test('test1')` |
      | **Shows intent** | Demonstrates desired API | Obscures what code should do |
      
      ## Why Order Matters
      
      **"I'll write tests after to verify it works"**
      
      Tests written after code pass immediately. Passing immediately proves nothing:
      - Might test wrong thing
      - Might test implementation, not behavior
      - Might miss edge cases you forgot
      - You never saw it catch the bug
      
      Test-first forces you to see the test fail, proving it actually tests something.
      
      **"I already manually tested all the edge cases"**
      
      Manual testing is ad-hoc. You think you tested everything but:
      - No record of what you tested
      - Can't re-run when code changes
      - Easy to forget cases under pressure
      - "It worked when I tried it" ≠ comprehensive
      
      Automated tests are systematic. They run the same way every time.
      
      **"Deleting X hours of work is wasteful"**
      
      Sunk cost fallacy. The time is already gone. Your choice now:
      - Delete and rewrite with TDD (X more hours, high confidence)
      - Keep it and add tests after (30 min, low confidence, likely bugs)
      
      The "waste" is keeping code you can't trust. Working code without real tests is technical debt.
      
      **"TDD is dogmatic, being pragmatic means adapting"**
      
      TDD IS pragmatic:
      - Finds bugs before commit (faster than debugging after)
      - Prevents regressions (tests catch breaks immediately)
      - Documents behavior (tests show how to use code)
      - Enables refactoring (change freely, tests catch breaks)
      
      "Pragmatic" shortcuts = debugging in production = slower.
      
      **"Tests after achieve the same goals - it's spirit not ritual"**
      
      No. Tests-after answer "What does this do?" Tests-first answer "What should this do?"
      
      Tests-after are biased by your implementation. You test what you built, not what's required. You verify remembered edge cases, not discovered ones.
      
      Tests-first force edge case discovery before implementing. Tests-after verify you remembered everything (you didn't).
      
      30 minutes of tests after ≠ TDD. You get coverage, lose proof tests work.
      
      ## Common Rationalizations
      
      | Excuse | Reality |
      |--------|---------|
      | "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
      | "I'll test after" | Tests passing immediately prove nothing. |
      | "Tests after achieve same goals" | Tests-after = "what does this do?" Tests-first = "what should this do?" |
      | "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
      | "Deleting X hours is wasteful" | Sunk cost fallacy. Keeping unverified code is technical debt. |
      | "Keep as reference, write tests first" | You'll adapt it. That's testing after. Delete means delete. |
      | "Need to explore first" | Fine. Throw away exploration, start with TDD. |
      | "Test hard = design unclear" | Listen to test. Hard to test = hard to use. |
      | "TDD will slow me down" | TDD faster than debugging. Pragmatic = test-first. |
      | "Manual test faster" | Manual doesn't prove edge cases. You'll re-test every change. |
      | "Existing code has no tests" | You're improving it. Add tests for existing code. |
      
      ## Red Flags - STOP and Start Over
      
      - Code before test
      - Test after implementation
      - Test passes immediately
      - Can't explain why test failed
      - Tests added "later"
      - Rationalizing "just this once"
      - "I already manually tested it"
      - "Tests after achieve the same purpose"
      - "It's about spirit not ritual"
      - "Keep as reference" or "adapt existing code"
      - "Already spent X hours, deleting is wasteful"
      - "TDD is dogmatic, I'm being pragmatic"
      - "This is different because..."
      
      **All of these mean: Delete code. Start over with TDD.**
      
      ## Example: Bug Fix
      
      **Bug:** Empty email accepted
      
      **RED**
      ```typescript
      test('rejects empty email', async () => {
        const result = await submitForm({ email: '' });
        expect(result.error).toBe('Email required');
      });
      ```
      
      **Verify RED**
      ```bash
      $ npm test
      FAIL: expected 'Email required', got undefined
      ```
      
      **GREEN**
      ```typescript
      function submitForm(data: FormData) {
        if (!data.email?.trim()) {
          return { error: 'Email required' };
        }
        // ...
      }
      ```
      
      **Verify GREEN**
      ```bash
      $ npm test
      PASS
      ```
      
      **REFACTOR**
      Extract validation for multiple fields if needed.
      
      ## Verification Checklist
      
      Before marking work complete:
      
      - [ ] Every new function/method has a test
      - [ ] Watched each test fail before implementing
      - [ ] Each test failed for expected reason (feature missing, not typo)
      - [ ] Wrote minimal code to pass each test
      - [ ] All tests pass
      - [ ] Output pristine (no errors, warnings)
      - [ ] Tests use real code (mocks only if unavoidable)
      - [ ] Edge cases and errors covered
      
      Can't check all boxes? You skipped TDD. Start over.
      
      ## When Stuck
      
      | Problem | Solution |
      |---------|----------|
      | Don't know how to test | Write wished-for API. Write assertion first. Ask your human partner. |
      | Test too complicated | Design too complicated. Simplify interface. |
      | Must mock everything | Code too coupled. Use dependency injection. |
      | Test setup huge | Extract helpers. Still complex? Simplify design. |
      
      ## Debugging Integration
      
      Bug found? Write failing test reproducing it. Follow TDD cycle. Test proves fix and prevents regression.
      
      Never fix bugs without a test.
      
      ## Testing Anti-Patterns
      
      When adding mocks or test utilities, read @testing-anti-patterns.md to avoid common pitfalls:
      - Testing mock behavior instead of real behavior
      ---
      name: "Spreadsheets"
      description: "Use skill when user requests to create, modify, analyze, visualize, or work with spreadsheet files (`.xlsx`, `.xls`, `.csv`, `.tsv`) or Google Sheets with formulas, formatting, charts, tables, and recalculation. Do not use for live controlling Microsoft Excel app or a live Excel session."
      ---
      
      # Spreadsheets skill
      Read entirely for spreadsheet creation, editing, analysis, or visualization.
      
      ## Decision Boundary
      - Google Sheets targeted outputs also require `routing/google_sheets.md`. Otherwise, author local files with artifact tool.
      
      ## Important Instructions
      - For new workbooks or authorized redesigns, plan the simplest correct workbook that meets the task, audience, actual data and domain. If formulas become hard to read, first reconsider whether the workbook’s structure, layout, or logic is overcomplicated before simplifying individual formulas. Remove unnecessary or duplicated logic while preserving calculation correctness, required business relationships, and financial reconciliation
      - Instruction precedence for workbook content, layout, and formatting is: user request > reference/template > domain defaults/conventions > general defaults.
      
      ## Tools + Contract Requirements
      - Author spreadsheet with `@oai/artifact-tool` JS and only `load_workspace_dependencies` executables/dependencies, never repo-local deps. If unavailable, check `~/.cache/codex-runtimes/codex-primary-runtime/dependencies/`. Never modify dependency directories.
      - In a writable, conversation-specific or tmp directory, create a `node_modules` symlink or Windows junction to the loader `node_modules`.
      - Prefer to patch/rerun one `.mjs` builder. No heredocs or duplicate builders.
      - Use the provided API reference for supported syntax. Its examples do not set workbook structure, formatting or formula defaults. Do not inspect package internals or prototypes. If blocked, run at most one targeted `workbook.help("<api_or_feature>")` query.
      - No `openpyxl`, `xlsxwriter`, or `pandas.ExcelWriter` authoring unless asked, or  `@oai/artifact-tool` is unavailable.
      - Analyze with JS/formulas, else bundled Python (libraries) and JSON/CSV intermediates; other libraries only for missing capabilities.
      - Use `update_plan` for complex work.
      - In your final response, omit builders, previews, or other support files unless requested.
      - Immediately before the first create/edit authoring command, run `mark_artifact_operation_started.mjs` successfully exactly once using the command below. Do not run it for read-only work. For edits, replace `create` with `edit`; adjust the expected count and output format to match the requested outputs.
        ```bash
        node container_tools/mark_artifact_operation_started.mjs --operation-kind create --expected-output-count 1 --output-format xlsx
        ```
      
      ## Spreadsheet (Workbook) Complexity: Workbook Structure & Formulas
      
      Keep the workbook simple, especially for focused tasks. A focused task produces a simple analysis, report or tracker for a specific question or workflow. It needs one main output, supported by the necessary inputs and calculations. “Focused” describes the scope of the task, not the number of source records.
      
      Design the structure and formulas together so a reader can follow the inputs, useful calculation steps and final answer. Put summaries and main outputs first, show the work behind them, and avoid tabs or formulas that only repeat finished results. Keep separate schedules and output views when they serve distinct needs. Preserve required detail, the supplied template and the requested edit scope.
      
      ## Workbook Structure
      
      ### Tab Types & Relationships
      
      Tab types describe the role each part of the workbook plays. They do not require separate tabs. A simple workbook can combine inputs, assumptions, builds and outputs in clearly labeled sections on one worksheet.
      
      **Inputs/Sources and Assumptions feed Builds; Builds calculate results and feed Outputs.** These relationships describe how calculations flow, not the physical tab order. The same rules apply when roles share a tab.
      
      **Input / Sources** contain the data the workbook starts from. Keep dedicated raw source or Actuals areas intact, with original values and source meaning separate from prepared calculations. Cleaning, mapping and source summaries may have their own labeled areas with clear provenance. Put business calculations, including historical calibration from actuals, in the build. Raw source data does not read results back from downstream areas.
      
      **Assumptions** hold the editable drivers and controls used by the builds. When cases are needed, keep one authoritative Case selector on Cover or Assumptions. Group each driver with its `Active Selection` row first, followed by its labeled case inputs, such as Base and Downside, sharing the same period columns. Prefer these driver groups to separate whole-case blocks for new designs. The build links directly to each period's active input. Preserve a supplied layout during narrow edits, and do not add cases or a separate tab when the task does not need them.
      
      Changing the Case selector updates the active forecast assumptions for each period. The same build keeps linking to those active cells and recalculates with the selected values. Outputs update from the build results while historical actuals remain unchanged.
      
      When cases are used, display the selected case on each worksheet by linking to the authoritative selector. Keep only one editable selector; distinguish source actuals and separately labeled comparison cases from the active forecast.
      
      In historical periods, the active assumption row may link to ratios or other measures calculated from actuals in a build. Show that history once, aligned with the build's historical period columns, to help the user set forecast assumptions. The forecast active row selects the chosen case's assumptions and feeds the build. Forecast results must not feed back into the assumptions driving that same forecast. Historical calibration is a business calculation, not a terminal Check/Audit result.
      
      **Build** tabs pull source inputs and assumptions to combine historical analysis, current results and/or a forecast. Bring the relevant inputs and applicable assumptions into clearly labeled rows or columns, then calculate the results on the build. Keep periods aligned and chronological. Show meaningful steps, subtotals and totals so readers can follow the logic—for example, headcount and compensation driving personnel cost, or revenue less COGS producing gross profit. Each step should do useful work. Do not hide the whole calculation in one dense formula or make the build merely repeat finished results from elsewhere.
      
      For a simple calculation, a small labeled assumption block can sit beside it. For a larger build, link important drivers from their control area and show the useful calculation steps. Use one set of forecast schedules driven by the active assumptions, organized by the business sequence, such as revenue, headcount, vendors and cash. Do not mirror the Assumptions grid, add Case columns or parallel named-case forecasts, or apply the selector only to finished results.
      
      A requested case comparison still needs each case's correctly evaluated results. If the requested simultaneous current results cannot be produced with the supported single-build design, explain the limitation and agree on the calculation or refresh method before building the comparison. Do not omit it, link both cases to the active result, or silently substitute snapshots, `TABLE`, arrays, dense formulas or a hidden second build. Preserve explicit user/template requirements and the separately authorized native-feature and capture workflows below.
      
      **Output / Summary** tabs consolidate the builds and tell the main story. These might be named “Overview,” “Summary,” “Exec Summary” or “Dashboard,” depending on the task. Bring across finished build results, show how matching totals roll into higher-level totals and put the main summary above the detail. Readers should be able to trace a headline result to its supporting build without finding the same calculation repeated elsewhere. Keep input retrieval, case selection and detailed business logic in the owning build/control area. Do not route forecast results through Assumptions before presenting them. Historical references used to set drivers and linked case/period displays remain allowed.
      
      **Check / Audit** tabs review source data and builds for completeness, consistency and reconciliation. They may calculate their own diagnostics, but do not own business calculations or feed assumptions, builds or outputs. Nothing outside the check/audit area should depend on its results.
      
      **Cover, if useful** gives a complex workbook a simple front page, especially for recurring or shared workflows. Include the company/project name or available logo, workbook title and relevant period or as-of date, with generous whitespace and restrained branding. Place it first. Keep analysis and methodology off the cover. Skip it for focused tasks or when the main output provides enough context.
      
      For complex workbooks, use a separate `ReadMe` only when source choices, joins, scoring or refresh steps need more explanation than nearby notes. Explain the method and material limitations without repeating outputs or giving a tab tour. Put it last. Multiple sources alone do not require one.
      
      Apply [Style guidance](style_guidelines.md) to these tab and section roles, so formatting helps readers distinguish the main answer, editable inputs and supporting calculations.
      
      ### Tab Names
      
      Use concise names that describe each tab's purpose, such as `Check` or `Audit` for a reconciliation tab. Preserve established names during unrelated edits. For new forecast work, use `Forecast review` for review checks, `Forecast variance` for comparisons with a prior forecast, or `Sensitivity` for assumption tests. Do not label these tabs or views `Movement` or `Forecast movement`.
      
      ### Tab Order & Progression
      
      For a new workbook or authorized redesign, start with one clear primary view that answers the task. Start with one tab, or two when the original source needs to stay separate, for focused tasks such as a department budget versus actuals report, a peer-company valuation comparison, a weekly marketing campaign report, an appointment-capacity tracker or a research measurement log with unit conversions. Preserve required source tabs and dependencies. Put the requested summary above the supporting detail and calculations. Add another tab only for a distinct source, calculation, reader or workflow need; do not create a separate tab for every role. Keep review commentary, refresh instructions and documentation beside the relevant work when they do not need a separate workflow.
      
      Keep separate schedules when the work requires them, such as revenue, payroll, depreciation and debt builds in a financial model. One or two tabs is a starting point for the examples above, not a limit on every workbook. Do not shrink text, hide necessary calculations or discard records to meet a tab count or fit one printed page. Preserve the supplied template and existing architecture during narrow edits.
      
      | Domain and task | Do: one output tab | Don't: create extra output/build tabs by default |
      | --- | --- | --- |
      | Finance / FP&A: one department's monthly budget versus actuals | On `Budget vs Actuals`, tab name `BvA`, show total spend and variance at the top, with category-level budget, actuals and variance calculations below. | Separate Summary, Dashboard, Scenarios and Assumptions tabs for this report. |
      | Financial modeling: peer-company valuation comparison from supplied data | On `Comparable Companies`, tab name `Comps`, show the requested multiple summaries at the top, with peer-company inputs and calculated multiples below. | A DCF, debt schedule or full three-statement model when the task only asks for comparable-company analysis. |
      | Marketing: weekly campaign spend and cost per lead | On `Campaigns`, show total spend, leads and overall cost per lead at the top, with campaign detail below. Calculate overall cost per lead from the matching totals. | One output tab per campaign, a duplicate dashboard or an attribution model that wasn't requested. |
      | Healthcare administration: appointment capacity by clinic | On `Appointments`, tab name `Appts`, show available slots, bookings and overall utilization at the top, with clinic and period detail below. Calculate overall utilization from the matching totals. | A separate dashboard, clinical alerts or a payroll schedule for an appointment report. |
      | Scientific research: measurement log with required unit conversions and a requested summary | On `Measurements`, show the requested results at the top, with original observations, units and required conversions below. | Separate Protocol, Processing, Calculations and Checks tabs, or statistical tests that the task does not require. |
      
      One output worksheet can contain several useful sections. Keep original sources and substantial builds separate when needed; do not create multiple output tabs for the same answer.
      
      For a file with multiple tabs, the physical left-to-right order is **Outputs → Builds → Inputs/Sources/Internal**, with a separate **Assumptions** control panel kept easy to reach, usually just after the primary output and before build tabs. Covers, key outputs (executive summary, financial statements, etc.) belong toward the left; working builds sit in the middle when needed; data, sources, inputs and internal documentation sit toward the right. A two-tab workbook has Output on the left and Input on the right. The logical calculation flow is Source/Input and Assumptions → Build → Output; a visible control panel may sit to the left of its builds. Do not confuse tab position with calculation sequence. Within a horizontal build, factors may feed intermediate results from left to right; preserve chronological period columns. Within a single worksheet, inputs and supporting calculations below can feed the main answer above. Preserve an intentional user/reference layout; do not reorganize a narrow edit to enforce this default.
      
      #### Checks and Audit
      
      Checks/Audit are terminal review areas and are not required for focused tasks. They read source/build evidence and may calculate or summarize their own diagnostics within that area. No formula outside a terminal check/audit area may use its results, directly or through helpers, names or dynamic references. This includes assumptions, business calculations, summaries, presented outputs, displayed statuses and output gates. Keep necessary input validation in the owning input/build logic; checks observe it independently. When separate tabs are useful, keep Checks/Audit and internal documentation toward the right. In complex workbooks, a divider such as `Internal >>` can group them with source data; follow [Style guidance](style_guidelines.md) for divider and child-tab colors. Preserve useful supplied controls and notes, but do not add separate tabs for a few lines.
      
      
      ### Build Structure and Formula Flow
      
      Arrange labeled rows and columns so a reader can follow starting data, assumptions, useful calculation steps, subtotals and results. Follow the physical layout above; the logical sequence of inputs to results does not require every build to run from top to bottom.
      
      - **Row progression:** make the useful business steps visible, such as quantity × rate, capacity used ÷ capacity available, or a balance plus its movements. Link the clean input and applicable assumption into their own labeled rows, then calculate the result on that build. Do not add trivial steps just to create more rows.
      - **Active assumptions:** select the active assumptions once in the control area and link each period's cells directly into the same build. Do not bypass the active row, repeat case selection across schedules, put a forecast inside Assumptions or maintain parallel case builds. Resolve a required comparison's calculation and refresh method as described in [Tab Types & Relationships](#tab-types--relationships).
      - **Historical reference:** Assumptions may link to historical ratios calculated from actuals in a build to help set forecast drivers. Trace the cells: this actuals-only reference must not create a feedback loop from the forecast into its own assumptions.
      - **Column progression:** keep comparable items, scenarios and periods aligned. Use the shared headers and controls described in [Anchoring](#anchoring) and [Dates and Time Periods](#dates-and-time-periods), rather than repeating them beside each calculation.
      - **Roll-forwards:** show opening balance, relevant movements and closing balance. Normally link each new period's opening balance to the prior period's closing balance, preserving the model's actual timing and conventions.
      - **Reuse:** keep one place that owns each calculation, then link matching results into summaries and useful output views. Apply the matching-input, period, unit, rounding and override conditions in [Formula Construction](#formula-construction).
      
      A tab that only repeats linked values from another tab or workbook is a red flag. Build tabs should perform useful calculations and show the steps. Output tabs should bring results together and calculate relevant subtotals or totals where needed. A useful output may link directly to completed build results without adding new calculations. Keep a linking-only tab when it serves a clear source, import or reporting need; otherwise, combine or remove it within the authorized scope. Do not invent calculations merely to justify a distinct reader view.
      
      ### Workbook Structure Examples
      
      | Example | Do | Don't |
      | --- | --- | --- |
      | A1. Simple action tracker | Use one `Actions` tab with owner, due date, status and the requested totals above the table. | Add Cover, Readme, Inputs, Dashboard and Checks tabs around a small task list. |
      | A2. Newly designed monthly activity report | Keep Month as a column in one activity table; use that table directly or add a linked summary tab to its left. | Copy the same layout into Jan, Feb and Mar tabs when separate monthly sheets are not required. |
      | A3. Compare several teams or campaigns | Keep the comparison in one table with a team/campaign field and the requested measures. | Create a separate nearly identical report tab for each team and make the reader assemble the comparison. |
      | A4. A few shared assumptions | Put a short labeled rate/assumption block to the left of the working calculation, or below the results on one worksheet. | Create Setup and Assumptions tabs for three cells, or duplicate editable copies of the same rate. |
      | A5. A requested scenario comparison | Group each driver's Active Selection and case inputs together. Keep one active build. Agree on any required comparison's calculation and refresh method, and label retained results accurately. | Maintain parallel case forecasts, omit the comparison or affected dependencies, link both cases to the active result, or use `TABLE` or snapshots as an ordinary shortcut. Do not add unneeded scenarios. Preserve explicitly required native sensitivity or [capture workflows](#circular-references-and-iterative-calculation). |
      | A6. Explain a one-page operating calculation | Put People needed at the top, the work/capacity calculation beneath it, and Requests and Minutes per request below. Let the lower inputs feed the answer above. | Scatter each step across a different tab, bury the answer at the bottom, or show only an unexplained staffing result. |
      | A7. Present an existing calculation | In a new multi-tab workbook, put Outputs on the left, Builds in the middle and Sources/Inputs on the right. Link the output to the completed build; on one worksheet, show that output above its build. Keep each editable control authoritative in one place; preserve an intentional front-end selector. | Put the primary output after internal source tabs, duplicate the same editable control in several places, create an unintended circular calculation, or rebuild the same calculation in the summary. |
      | A8. Reconcile a small import | Put an independent comparison near the relevant table. Use a Checks/Audit tab only if needed, and keep it a terminal reader of sources and builds. | Add a full control dashboard for one useful tie-out, or make the build, summary or output gate read a Checks/Audit result. |
      | A9. Keep source context usable | Document each source once alongside the relevant input data, following [Citation Requirements](#citation-requirements). Retain essential period/unit labels, required row-level source columns and intact source tabs. | Repeat filenames and source explanations across builds and outputs, hide essential context in cell notes, or create Sources, Notes, Methodology and Version History tabs for a one-off analysis with one source. |
      | A10. Summarize a long source table | Keep all required records intact and make the primary view compact. Use a separate source tab when it improves use or preserves the import. | Drop rows, hide needed calculations or make text tiny so all the evidence fits on one page. |
      | A11. A production plan with distinct schedules | Keep materials, line-capacity and staffing schedules separate when their inputs, time grains or update owners differ; place the primary output plan to the left of those builds, with supporting data/inputs farther right. | Merge incompatible schedules just to stay within two tabs, or repeat their calculations in the summary. |
      | A12. A narrow edit to an existing workbook | Change the requested cells and affected dependencies, preserving established tabs, native features and layout. | Normalize, merge, rename or remove existing tabs just because a new workbook could be simpler. |
      | A13. Several thin tabs around one calculation | For a new capacity plan, keep the input factors, meaningful work/capacity calculation and requested result together in one view or two useful tabs. A Build should contribute the steps shown in F13. | Create seven tabs that mostly repeat the same central range, with nominal Build tabs doing no distinct work. Putting that central calculation on Checks/Audit is also a dependency failure. |
      | A14. More than one output view | Keep an operator detail view and a manager summary when their fields, level of detail or workflow differ. Both may link to the same owning build, as in F14. | Copy the same table into Summary, Dashboard, Report and Executive tabs without a distinct reader need, or invent new calculations just to make each tab look different. |
      
      
      ## Formulas
      
      Apply these rules to newly added or edited formulas and their affected dependencies. Follow the user's preferences and supplied template; preserve unrelated formulas and layout during narrow edits. Design formulas to support the workbook structure above: the reader should be able to follow the inputs, useful calculation steps and final answer.
      
      ### Formula Construction
      
      - Use direct references, familiar functions and meaningful intermediate calculations. Follow [Build Structure and Formula Flow](#build-structure-and-formula-flow) to show the work; do not hide an entire build in one dense formula or add trivial helpers just to make formulas shorter.
      - Keep raw data, editable assumptions, mappings and business rules in labeled cells or tables. Mathematical, index and control constants may remain in formulas. Keep calculated results as formulas so they update with their inputs.
      - Fixed cutoffs or categories from the user's request can appear directly in formulas when result labels state the rule. For example, label `COUNTIFS(B2:B100,">1000")` as `Invoices over $1,000`, without adding an input cell for `1000`. Use one labeled input cell when the cutoff is user-adjustable or serves as a shared assumption across different calculations.
      - Calculate a shared result once and reuse it when the inputs, period, units, rounding and overrides match. Keep independent reconciliations independent.
      - Use consistent formulas across comparable rows and periods, while preserving intentional differences such as [historical versus forecast logic](domain_guidance/financial_models.md#periods-assumptions-and-scenarios), one-off adjustments and overrides.
      - Keep business calculations in the owning build and necessary input guards with their inputs or dependent build logic, following the [terminal Checks/Audit rule](#checks-and-audit). Do not invent business restrictions or wrap ordinary calculations in repeated workbook-wide validation gates. For example, use `=SUM(I11:I12)` for a valid total; do not add an `IF` that rejects a negative result unless the business rule requires it.
      
      ### Anchoring
      
      Use `$` to fix only the part of a reference that must stay in place when a formula is copied. Anchor shared **rows, columns or individual cells** so the workbook can reuse one period header, assumption block, item column or Case selector instead of repeating it beside every calculation.
      
      | Reference | What stays fixed | Useful pattern |
      | --- | --- | --- |
      | `C8` | Neither row nor column | A quantity that moves with the calculation when copied across or down. |
      | `C$4` | Row 4 | Read each column's period from one shared header row; copying across advances the period, copying down keeps that header. |
      | `$A8` | Column A | Read each row's item or category from one shared column; copying down advances the item, copying across keeps its label. |
      | `$B$3` | Cell B3 | Reuse one fixed conversion rate or Case selector throughout the applicable calculation. |
      
      For example, `=SUMIFS(Amount,Month,C$4,Item,$A8)` reads the period above and the item at the left. Copied one column right it uses `D$4`; copied one row down it uses `$A9`. The aligned named ranges represent the source columns; they do not require named ranges in the delivered workbook.
      
      A period-specific assumption should move with its period: `=C8*C$3` becomes `=D8*D$3` when copied across. A single assumption shared by every period should stay fixed: `=C8*$B$3` becomes `=D8*$B$3`. Choose between them from the model's meaning, not by adding `$` everywhere. Use keyed lookups when source and destination orders differ; anchoring cannot make mismatched row positions equivalent. Quote cross-sheet names, for example `='Build'!E14`.
      
      ### Dates and Time Periods
      
      - When calculations depend on a reporting date, use the date specified by the task or source. Use TODAY() only when calculations should update with the current date. Use a fixed reporting date when results should remain tied to a particular date. Label any assumed date. Preserve source deadlines and flag conflicts with derived deadlines.
      - Review the template's calendar, period layout and source grain before building formulas. Use real dates where the source supports them, with number formats for display; do not invent a missing reporting year. Derive period filters and labels from the shared header rather than hardcoding months in individual formulas.
      - For a new `Week of` label, use the week's first business day as the underlying date: Monday by default, moved forward for holidays only when a holiday calendar is supplied. Follow an explicit source/template week convention. Do not invent holidays or relabel a week-ending date as a week start.
      - When several time scales are needed and the template does not prescribe a layout, place the broader summaries to the left and finer detail to the right: **Annual | Quarterly | Monthly | Weekly**. Include only the time scales needed for the task. Keep periods chronological from left to right within each group; use the supplied fiscal calendar and week convention.
      - Separate different time scales with narrow, blank, unfilled spacer columns; do not extend formatting down the entire column. Do not add a spacer merely between actual and forecast months in one continuous schedule. Align matching period columns across Assumptions, builds and summaries where practical. When recent actuals help set drivers, include that historical reference on Assumptions in the same period column as the build, followed by the matching forecast periods. Within a continuous schedule, use one shared period header rather than repeating identical date rows above every subsection. Keep it visible when useful; separate tables with different column meanings may need their own headers, and print titles can repeat headers on printed pages.
      - Match each period to its own assumptions and data. Roll detail into summaries using the right calculation: sum additive amounts, use the appropriate ending balance for stocks, and calculate ratios or weighted averages from the relevant components. Do not sum monthly percentages or double-count weeks that cross month boundaries.
      
      For a monthly summary of daily dates, with `C4` holding the first day of the month and aligned source ranges, use `=SUMIFS(Amount,Date,">="&C$4,Date,"<"&EDATE(C$4,1),Item,$A8)`. The next-month exclusive upper bound includes the full last day, including timestamps. Equality to `C$4` is appropriate only when the source already stores that same monthly key.
      
      ### Choosing Formulas and Excel Tools
      
      - **Totals and products:** use `SUM` over the relevant detail for total rows. Use `PRODUCT` for a result built by multiplying a range of numeric factors, or direct multiplication for a simple two-cell calculation. Use `SUMPRODUCT` for a sum of matching quantity × rate pairs or a weighted calculation. Keep ranges aligned and bounded; do not include both subtotals and their detail. Check required factors first: `PRODUCT` ignores blank/text cells in a referenced range, which can make missing inputs look like a valid result.
      - **Conditional counts, sums and averages:** prefer `COUNTIFS`, `SUMIFS` and `AVERAGEIFS` for new formulas, even with one criterion, so another condition can be added consistently. Avoid choosing `COUNTIF`, `SUMIF` or `AVERAGEIF` for new work by default; preserve a valid existing/template convention during a narrow edit. This preference does not prohibit an ordinary `IF` condition.
      - **Lookups:** `INDEX/MATCH`, `VLOOKUP` and `XLOOKUP` are all useful. Follow the user's preference and the workbook's established approach where it works. Make exact versus approximate matching intentional, handle missing keys explicitly and confirm whether duplicate keys should be rejected, matched once or aggregated. Do not substitute a first-match lookup for a required sum.
      - **Conditional logic:** use a short `IF` for a simple choice. Nested `IF` formulas are appropriate when they express necessary, understandable logic, including advanced Finance calculations. For a long list of categories or editable rules, prefer a mapping table or labeled steps. Preserve rule order, boundaries, gaps and the unmatched case; do not replace useful business logic merely to reduce nesting.
      - **Formula choices to avoid:** do not introduce `LET`, array/spill formulas, `MAP`, `REDUCE` or `LAMBDA`. Use familiar formulas and labeled intermediate steps. Normal range arguments in functions such as `SUMIFS` and `SUMPRODUCT` remain appropriate, as do the lookup, `INDIRECT`, `OFFSET` and `CHOOSE` patterns below. Preserve required existing/template behavior and do not rewrite unrelated formulas during a narrow edit. Formula length alone is not the test: the reader must be able to understand and extend the calculation.
      - **Sensitivity analysis:** use a native What-If Data Table only for an explicitly requested native sensitivity analysis or required existing/template behavior, when supported. Do not introduce `TABLE` into an ordinary forecast or case comparison, or manufacture a second varying input with a metric selector. Excel supports one or two varying inputs; the current Artifact Tool supports only two-variable tables, with both input cells on the table’s worksheet. Read [Data Tables](artifact_tool_docs/DATA_TABLES.md) before creating one. Two inputs test one output across their combinations; use separate tables for additional outputs. If the requested native design is unsupported, explain the limitation before agreeing on a formula-based design or change-input/recalculate/restore process. Label captured results and their refresh method. Ordinary case comparisons follow the single-build and comparison boundary above.
      
      An Excel Table, PivotTable and What-If Data Table are different features. Check the chosen tool and destination's support. If a requested native feature cannot be created or preserved, explain the limitation before substituting a formula or static result. Keep API setup and feature-specific execution details in the relevant tool reference.
      
      ### Scalable Formulas and Brief Explanations
      
      Use the patterns below when they make recurring updates easier without hiding the calculation. Choose the simplest approach that supports the actual update workflow, not just the current snapshot.
      - **Assumption and Case selection:** prefer one numeric Case selector with labeled case names and `CHOOSE` or `OFFSET` to select the active assumptions. `INDEX/MATCH` or `XLOOKUP` remain valid when they fit the layout. In each driver group, put Active Selection above its case inputs, sharing the same period header. For example, with Case in B3 and two case values in I22:I23, active I21 can be `=CHOOSE($B$3,I22,I23)`; the matching build input is simply `='Assumptions'!I21`. Anchor and validate the selector. Do not repeat the choice in the build or maintain a second editable copy of the drivers. The simple CHOOSE example assumes validated numeric case inputs. Otherwise, test the selected source value before a reference can turn a blank into zero. Preserve a valid zero. A missing unselected case must not block the active case. In an agreed comparison, mark only the affected case and dependent deltas unavailable. Keep necessary validation local to the driver and reuse it. OFFSET and INDIRECT are volatile, so keep references bounded and consider recalculation cost.
      - **New monthly source tabs:** if the workflow receives a separate tab in the same format each month, a visible month-to-tab registry and bounded `INDIRECT` references can support new periods without rewriting the reference pattern. Register the new tab and extend the summary periods or bounded ranges when needed. Validate the expected layout, tab names and source coverage; quote and escape sheet names correctly. For a new workflow without that constraint, one source table with a Month column may be simpler.
      - **Explain recurring updates:** when a less familiar formula materially improves the workbook, add a short explanation near its control or in the existing guide: why it helps, what the user can change and how to extend it safely. For example: “Add the new month tab in the same layout and register its name in Setup. Extend the summary period and ranges if needed; the formulas keep the same reference pattern.” Keep this brief; do not add comments to every formula or create a new instruction tab for one note.
      
      ### Missing Inputs, Errors and Overrides
      
      - Do not invent missing source data or substitute a different metric. If required data is absent, leave the result unavailable and state the specific missing input beside its data or setting and briefly in the response. For a rate, preserve the requested numerator, denominator, population and period; do not substitute another available denominator.
      - Distinguish a real zero from missing data, an unavailable result and something that is not applicable. Use `"n.a."`, a deliberate `""` blank, or an exposed error according to the user's preference and the calculation's meaning. Right-align `n.a.` and similar placeholders when they sit among numeric results; do not turn them into numeric zero for appearance.
      - `IFERROR` can be useful for a deliberate, understood fallback, but must not hide unexpected failures. Prefer testing the expected condition directly, or `IFNA`/a lookup's not-found result when only a missing match is expected. Do not blanket-wrap formulas in `IFERROR(...,0)` or `IFERROR(...,"")` to make broken references and bad inputs disappear. Text `"n.a."` and the `#N/A` error are different; choose intentionally and ensure downstream formulas handle the result correctly.
      - Guards such as `ISNUMBER` must not turn a failed prerequisite into a healthy zero or an understated issue count. Keep unexpected failures visible in the affected results, even when an intermediate formula returns text or a blank instead of an error.
      - Handle necessary validation in the input/build that owns it, affecting only the relevant outputs. A SUMIFS result of zero does not prove matching records exist; retain a source-coverage test when no match must remain blank or unavailable. Keep the issue visible without spreading the same long guard through every summary formula or pulling a global status from Checks/Audit.
      - A matched lookup key does not prove its value is populated. Check required source values before a lookup or reference can turn a blank into zero; preserve a permitted numeric zero.
      - Add manual overrides only when the task, template or established workflow needs them. Otherwise, calculate directly from the relevant drivers; do not add an optional override row to every result.
      - Preserve deliberate zero overrides, blanks, one-off adjustments and rounding. A blank optional override may mean “use the base”; a zero override may mean “use zero.” Do not treat those as the same condition.
      
      ### Circular References and Iterative Calculation
      
      Avoid unintended circular references. Use intentional circular logic only when the requested model needs it and the selected tool and target engine support it. Document the loop and its purpose; preserve or deliberately configure iteration, maximum iterations and maximum change. Verify convergence after representative input changes and save/reopen. Do not silently enable iteration, change application-wide settings, or treat cached values, a successful export or an error-free scan as proof. If calculation or setting preservation cannot be verified, report the limitation and use a verified workflow or a mathematically equivalent non-circular approach within scope. Keep Checks/Audit outside the loop.
      
      An explicit/template case-capture workflow may use a self-retaining `IF` in an output area to store a selected case's result while the same model calculates the other cases. This is a snapshot, not a live recalculation of every case; assumptions and business calculations must not depend on it. Define initialization and capture/refresh steps, show the captured case and stale-state warning, and verify each case is captured and retained correctly in the intended engine. Convergence alone does not prove capture correctness. Do not introduce this pattern as a default scenario comparison.
      
      Present case results as a compact `Case comparison`, with each case named above comparable metric rows and period columns. Keep capture/refresh instructions secondary and label saved snapshots clearly; a new label or layout does not make them live.
      
      ### Formula Examples
      
      These examples assume the inputs, ranges and units described. Named ranges stand for labeled source ranges, not a requirement to add names. Preserve the task's missing-data policy and material rounding.
      
      | Example | Do | Don't |
      | --- | --- | --- |
      | F1. Reuse an editable assumption | With one fixed conversion rate in B3, use `=C8*$B$3`. With a different rate in each period of row 3, use `=C8*C$3` and fill across. | Hardcode the rate in every formula, or let a shared rate drift to a neighboring cell when copied. |
      | F2. Show a build on one worksheet | Put Requests in B10 and Minutes per request in B9; calculate Work minutes in B8 as `=PRODUCT(B9:B10)`. With positive Available minutes per person in B7, put People needed in B6 as `=B8/B7`, with required whole-person rounding. All factors must be present and numeric. | Hide input retrieval, unit conversion and staffing logic inside one unexplained output, or treat a missing factor as zero workload. |
      | F3. Reuse the matching subtotal | If B12 is the eligible-volume subtotal for the required period, calculate `=B12*$B$3`. | Re-sum the detail in every output, or reuse a subtotal with different eligibility, units, period or rounding. |
      | F4. Link a period rollforward | Link this month's Beginning inventory to the prior month's Ending inventory; calculate Ending as Beginning + Receipts − Usage. | Rebuild cumulative history from the first month in every period when the prior ending balance already represents the same quantity. |
      | F5. Resolve a shared lookup once | With unique validated keys and matched ranges, put the rate in D8 with `=INDEX('Rates'!$C$5:$C$12,MATCH($A8,'Rates'!$A$5:$A$12,0))`; reuse D8 for that same rate. An established VLOOKUP or XLOOKUP pattern is also valid. | Repeat the same lookup in each output, silently select an ambiguous duplicate, or add a helper for an already simple one-use expression. |
      | F6. Replace a long category decision tree | Keep the category-to-owner mapping in a table; with unique keys, use `=XLOOKUP($A8,Categories,Owners,"Unmapped",0)`. | Repeat a long category `IF` chain in every row, or remove necessary conditional model logic merely because it uses nested IFs. |
      | F7. Preserve rule boundaries | For supplied bands `0 ≤ x < 100`, `100 ≤ x < 500`, and `x ≥ 500`, preserve those boundaries and test the thresholds and values on either side. | Turn `<100` into `≤100`, reorder overlapping tests, fill an intentional gap or invent a default category. |
      | F8. Guard the expected exception | With validated numeric B8 and C8 and a not-applicable policy for a zero denominator, use `=IF(C8=0,"n.a.",B8/C8)`. A deliberate blank may be appropriate under a different display policy. | Use `IFERROR(...,0)` so missing data or a broken reference appears to be a real zero rate. |
      | F9. Preserve a zero override | With base B8 and validated optional override C8, use `=IF(C8="",B8,C8)`. | Use `=IF(C8=0,B8,C8)` and erase a valid zero override, or overwrite the base to apply an adjustment. |
      | F10. Fill using shared headers and labels | Use `=SUMIFS(Amount,Month,C$4,Item,$A8)` for matching monthly keys. Row 4 supplies periods across the table; column A supplies items down it. Use the date-bounds pattern above for daily source dates. | Repeat the same date header in every subsection, hardcode January across the year, or assume differently ordered source tabs have matching row positions. |
      | F11. Choose the aggregate that matches the math | Use `=SUM(C8:C11)` for a total, `=PRODUCT(C8:C10)` for three required numeric factors, or `=SUMPRODUCT(B8:B11,C8:C11)` for matching quantity × rate pairs. Use SUMIFS for an ordinary conditional sum. | Replace these with a custom array pipeline, double-count subtotal rows, or let PRODUCT silently skip a missing required factor. |
      | F12. Keep checks independent and one-way | If a Checks tab is warranted, compare the build with an independent source control there, such as `='Build'!E14-'Source'!D20`. | Use `='Checks'!C8` in a build, summary or output gate, compare a total with itself, or treat a cached PASS as a newly executed check. |
      | F13. Show progression within a build | For A13's capacity plan, use numeric Runs in C8 and kWh per run in D8 to calculate Energy needed in E8 as `=C8*D8`. With positive Available kWh in F8 for the same period, calculate Capacity share in G8 as `=E8/F8`. | Label a linked copy “Build,” hide all factors in one long formula, or add relay tabs without useful work. |
      | F14. Share a result across useful views | For A14's distinct output views, let both read the owning result, such as `='Build'!E14`, and present the detail their readers need. | Recompute the same result in every output, or copy the same table into several tabs without a distinct reader or workflow need. |
      
      
      ## Writing Quality and Authored Content
      Apply these defaults to text you write, including titles, labels and messages returned by formulas. User instructions and preferences, reference/template conventions and domain guidance take precedence, in that order. For edits, do not change unrelated content outside of the user's request and follow the workbook’s existing writing style.
      
      - Write for the intended audience. Never include internal file paths, authoring commentary, planning notes, or requester instructions in the artifact unless explicitly requested. Do not repeat audience or style directives such as “executive-friendly” in headings, content, or comments.
        - Omit: `Discussion support only. This workbook does not make final rating or promotion decisions.` just because the user asked for a workbook for discussion.
        - Omit: `Supports discussion and consistency checks. Human reviewers remain responsible.` unless that limitation is explicitly required.
      
      - Include text only when it helps the reader understand the data or use the workbook. Keep clear text unchanged. Rewrite useful text that is unclear. Delete unnecessary text instead of replacing it with a cleaner version of the same filler.
      
      - Use concise, plain-language titles and labels. Name the specific subject, issue or action and avoid internal jargon and vague status labels. Preserve what each label measures, including the population, period, units, comparison, and uncertainty. Do not shorten a label by removing a distinction the reader needs.
        - Good: `Weekly metrics`. Bad: `Follow the weekly trends`
        - Use `Metric` for a general metric column and `Revenue driver` for a revenue assumption explanation. Avoid invented labels such as `Planning measure`, `Movement explanation` or `Planning basis`. Retain specific labels when they add necessary meaning.
        - Bad: `Requisition blockers`. Good: `Hiring requests awaiting approval` when approval is the issue.
        - Bad: `Two-band rating movement`. Choose a descriptive, clear phrase that represents the underlying event, e.g.:
          - Promotion: `Promoted by two job levels`
          - Rating change: `Performance rating increased by two levels`
        - Good: `Monthly results`. Bad: `Decision-ready monthly impact analysis`
        - Good: `Income and household assumptions`. Bad: `Same paycheck. Different purchasing power.`
        - Use `Retained employees` only for employees who remained over a defined period. Otherwise, name the population counted, such as `Total employees` or `Employees reviewed`.
      
      - Avoid decorative bullets, icons, emoji, arrows and pipe-delimited titles. Omit filler suffixes; keep terms such as `review`, `analysis` or `dashboard` when they identify the content.
        - Bad: `$ in USD • monthly • forecast`
        - Good: `Monthly forecast (USD)`
      
      - Prefer direct, specific human wording. Avoid slogans, buzzwords, invented terminology, vague framing and formulaic claims.
        - Good (when supported by the data): `Most revenue growth comes from data centers.` Bad: `Data centers are doing the heavy lifting.`
        - Good: `Contributions decreased`. Bad: `Contributions waned`
        - Good: `Revenue metrics`. Bad: `Strategic Value Drivers`
        - Bad formulaic phrasing: `The tool not only saves time, but also transforms how teams collaborate.` or `Faster, smarter, and more intuitive.`
        - Bad: `While remote work offers flexibility, it also presents unique challenges.` (synthetic balance without a real tradeoff)
        - Bad: `Operating evidence improved`. Operating evidence is unclear and not a common term used.
      
      - Avoid AI-like sentence constructions. Use direct sentences with clear meaning and avoid vague explanations and forced contrasts. Prefer periods between sentences. Do not use semicolons, pipes, bullets, or dashes to assemble several labels into a slogan.
        - Semicolons and vague explanations: Use `Travel demand and employment fell from Jan to Feb.`, not `Travel demand and employment fell from Jan to Feb; persistent behavior shifts are shaping the path back.`.
        - Passive voice when active is clearer e.g. Use `The team approved the proposal.` not `The proposal was approved by the team.`
        - Contrast slogans like `It’s not X, it’s Y`: For a title, use `Humidity exposure over time` not `Humidity is an exposure trajectory, not a setpoint.`
        - Unnecessary em-dashes: Bad: `Purpose: isolate what changed – and what deliberately stayed in place – under Osaka Prefecture’s Red Stage emergency response.`
      
      - Keep wording factual, parseable and supported by the workbook.
        - Good: `Transit use is 79% of pre-pandemic levels.`
        - Bad: `79% Transit use back to pre-pandemic`
      
      - Omit repeated information, obvious purpose statements and generic disclaimers. Subtitles are optional. State critical definitions and material assumptions once beside the relevant data or setting. Preserve task-required limits and warnings, such as a review supporting discussion rather than making final personnel decisions.
      
      - Do not include motivational wording or self-assessment. Omit decorative badges and self-evaluation banners. Preserve task-required business statuses, risk flags, uncertainty labels and specific warnings as ordinary data. Do not invent scoring systems or confidence scales merely to decorate the workbook.
        - Omit: `This workbook is source-backed and ready for review`.
      
      - For checks and logic, be specific:
        - Bad: `Signal integrity: BLOCKED`. Good: `Missing input: forecast rate` (a specific functional warning)
      
      - For a requested workflow, provide an obvious editable field for required human input, separate from original source notes. Short calculated statuses or actions should reflect all required prerequisites. Do not imply completion while another required action is still open.
      
      
      ## Workflows
      Required:
      - `workflows/edit_workflows.md` for existing files/follow-ups.
      - `workflows/create_workflows.md` for new files
      
      ## Resources
      Read the following BEFORE starting the task:
      
      Required:
      - `artifact_tool_docs/API_QUICK_START.md` for `artifact_tool` JS API documentation. Read entirely.
      - `style_guidelines.md` for formatting.
      
      As applicable:
      - `references/template-elicitation.md`: if user has not provided a template, reference, or visual direction.
      - `references/image-references.md`: if a reference image or screenshot is provided.
      - `references/read_only_qna.md`: for Q&/audits
      - `features/charts.md`: for creating or editing charts.
      
      <a id="domain-requirements"></a>
      
      ## Role and Domain Guidance
      Before authoring, identify the user's **task/function**, **role**, **audience** and **industry** separately, then read the relevant guides below. Apply the professional conventions of the work being done; a role or industry label alone does not determine the workbook's structure or formatting.
      - Use function guidance for the work being done. Financial forecasts, budgets, cash models and valuations use Finance guidance in any industry.
      - Add industry requirements only when they affect definitions, units, source handling or the workflow. A healthcare company's financial forecast uses Finance guidance; an appointment tracker does not inherit financial-model structure or colors.
      - Use the user's role and audience to choose useful detail, terminology and outputs, and to resolve ambiguity in the task. Do not apply Finance conventions to an unrelated task just because the user works in Finance. Explicit instructions and templates retain precedence; relevant domain conventions override generic defaults.
      
      Guides:
      - Finance, corporate finance and FP&A, financial modeling, valuation and investment banking: `domain_guidance/financial_models.md`. Read the relevant financial requirements below the shared structure, formula and style rules.
      - Healthcare: `domain_guidance/healthcare.md`
      - Marketing and advertising: `domain_guidance/marketing_advertising.md`
      - Scientific research: `domain_guidance/scientific_research.md`
      
      ## Create and Edits
      For any task that requires modifying or creating a workbook:
      
      ### Data Formatting Rules
      - Store numbers, percentages, currency, and dates as typed spreadsheet values, not preformatted strings. Use text only for true identifiers such as ZIP codes, account IDs, SKUs, or labels.
      - Use Excel-invariant number/date format codes, not locale-specific display strings. Generic numeric examples include `#,##0`, `#,##0.0`, `0.0%`, `0.00%`, `"$"#,##0`, `"$"#,##0.00`. Preserve source dates and unrelated existing formats.
      - Percentages: Follow the domain or reference's precision. Otherwise, use 1 decimal for most analytical cells, 0 decimals for dashboard outputs, and 2 decimals where small rate differences matter.
      - Do not swap `.` and `,` in format codes to mimic locale separators; separators are controlled by spreadsheet/render locale. Use `0.0%`, not `0,0%`, and `#,##0`, not `#.##0`.

## Activity

    $ /bin/zsh -lc "wc -l /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/SKILL.md /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/workflows/edit_workflows.md /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/artifact_tool_docs/API_QUICK_START.md /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/style_guidelines.md /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/domain_guidance/scientific_research.md && sed -n '1,240p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/SKILL.md && sed -n '241,520p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/SKILL.md"
    status: Completed · exit 0
           453 /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/SKILL.md
            24 /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/workflows/edit_workflows.md
           444 /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/artifact_tool_docs/API_QUICK_START.md
            62 /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/style_guidelines.md
            30 /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/domain_guidance/scientific_research.md
          1013 total
      ---
      name: "Spreadsheets"
      description: "Use skill when user requests to create, modify, analyze, visualize, or work with spreadsheet files (`.xlsx`, `.xls`, `.csv`, `.tsv`) or Google Sheets with formulas, formatting, charts, tables, and recalculation. Do not use for live controlling Microsoft Excel app or a live Excel session."
      ---
      
      # Spreadsheets skill
      Read entirely for spreadsheet creation, editing, analysis, or visualization.
      
      ## Decision Boundary
      - Google Sheets targeted outputs also require `routing/google_sheets.md`. Otherwise, author local files with artifact tool.
      
      ## Important Instructions
      - For new workbooks or authorized redesigns, plan the simplest correct workbook that meets the task, audience, actual data and domain. If formulas become hard to read, first reconsider whether the workbook’s structure, layout, or logic is overcomplicated before simplifying individual formulas. Remove unnecessary or duplicated logic while preserving calculation correctness, required business relationships, and financial reconciliation
      - Instruction precedence for workbook content, layout, and formatting is: user request > reference/template > domain defaults/conventions > general defaults.
      
      ## Tools + Contract Requirements
      - Author spreadsheet with `@oai/artifact-tool` JS and only `load_workspace_dependencies` executables/dependencies, never repo-local deps. If unavailable, check `~/.cache/codex-runtimes/codex-primary-runtime/dependencies/`. Never modify dependency directories.
      - In a writable, conversation-specific or tmp directory, create a `node_modules` symlink or Windows junction to the loader `node_modules`.
      - Prefer to patch/rerun one `.mjs` builder. No heredocs or duplicate builders.
      - Use the provided API reference for supported syntax. Its examples do not set workbook structure, formatting or formula defaults. Do not inspect package internals or prototypes. If blocked, run at most one targeted `workbook.help("<api_or_feature>")` query.
      - No `openpyxl`, `xlsxwriter`, or `pandas.ExcelWriter` authoring unless asked, or  `@oai/artifact-tool` is unavailable.
      - Analyze with JS/formulas, else bundled Python (libraries) and JSON/CSV intermediates; other libraries only for missing capabilities.
      - Use `update_plan` for complex work.
      - In your final response, omit builders, previews, or other support files unless requested.
      - Immediately before the first create/edit authoring command, run `mark_artifact_operation_started.mjs` successfully exactly once using the command below. Do not run it for read-only work. For edits, replace `create` with `edit`; adjust the expected count and output format to match the requested outputs.
        ```bash
        node container_tools/mark_artifact_operation_started.mjs --operation-kind create --expected-output-count 1 --output-format xlsx
        ```
      
      ## Spreadsheet (Workbook) Complexity: Workbook Structure & Formulas
      
      Keep the workbook simple, especially for focused tasks. A focused task produces a simple analysis, report or tracker for a specific question or workflow. It needs one main output, supported by the necessary inputs and calculations. “Focused” describes the scope of the task, not the number of source records.
      
      Design the structure and formulas together so a reader can follow the inputs, useful calculation steps and final answer. Put summaries and main outputs first, show the work behind them, and avoid tabs or formulas that only repeat finished results. Keep separate schedules and output views when they serve distinct needs. Preserve required detail, the supplied template and the requested edit scope.
      
      ## Workbook Structure
      
      ### Tab Types & Relationships
      
      Tab types describe the role each part of the workbook plays. They do not require separate tabs. A simple workbook can combine inputs, assumptions, builds and outputs in clearly labeled sections on one worksheet.
      
      **Inputs/Sources and Assumptions feed Builds; Builds calculate results and feed Outputs.** These relationships describe how calculations flow, not the physical tab order. The same rules apply when roles share a tab.
      
      **Input / Sources** contain the data the workbook starts from. Keep dedicated raw source or Actuals areas intact, with original values and source meaning separate from prepared calculations. Cleaning, mapping and source summaries may have their own labeled areas with clear provenance. Put business calculations, including historical calibration from actuals, in the build. Raw source data does not read results back from downstream areas.
      
      **Assumptions** hold the editable drivers and controls used by the builds. When cases are needed, keep one authoritative Case selector on Cover or Assumptions. Group each driver with its `Active Selection` row first, followed by its labeled case inputs, such as Base and Downside, sharing the same period columns. Prefer these driver groups to separate whole-case blocks for new designs. The build links directly to each period's active input. Preserve a supplied layout during narrow edits, and do not add cases or a separate tab when the task does not need them.
      
      Changing the Case selector updates the active forecast assumptions for each period. The same build keeps linking to those active cells and recalculates with the selected values. Outputs update from the build results while historical actuals remain unchanged.
      
      When cases are used, display the selected case on each worksheet by linking to the authoritative selector. Keep only one editable selector; distinguish source actuals and separately labeled comparison cases from the active forecast.
      
      In historical periods, the active assumption row may link to ratios or other measures calculated from actuals in a build. Show that history once, aligned with the build's historical period columns, to help the user set forecast assumptions. The forecast active row selects the chosen case's assumptions and feeds the build. Forecast results must not feed back into the assumptions driving that same forecast. Historical calibration is a business calculation, not a terminal Check/Audit result.
      
      **Build** tabs pull source inputs and assumptions to combine historical analysis, current results and/or a forecast. Bring the relevant inputs and applicable assumptions into clearly labeled rows or columns, then calculate the results on the build. Keep periods aligned and chronological. Show meaningful steps, subtotals and totals so readers can follow the logic—for example, headcount and compensation driving personnel cost, or revenue less COGS producing gross profit. Each step should do useful work. Do not hide the whole calculation in one dense formula or make the build merely repeat finished results from elsewhere.
      
      For a simple calculation, a small labeled assumption block can sit beside it. For a larger build, link important drivers from their control area and show the useful calculation steps. Use one set of forecast schedules driven by the active assumptions, organized by the business sequence, such as revenue, headcount, vendors and cash. Do not mirror the Assumptions grid, add Case columns or parallel named-case forecasts, or apply the selector only to finished results.
      
      A requested case comparison still needs each case's correctly evaluated results. If the requested simultaneous current results cannot be produced with the supported single-build design, explain the limitation and agree on the calculation or refresh method before building the comparison. Do not omit it, link both cases to the active result, or silently substitute snapshots, `TABLE`, arrays, dense formulas or a hidden second build. Preserve explicit user/template requirements and the separately authorized native-feature and capture workflows below.
      
      **Output / Summary** tabs consolidate the builds and tell the main story. These might be named “Overview,” “Summary,” “Exec Summary” or “Dashboard,” depending on the task. Bring across finished build results, show how matching totals roll into higher-level totals and put the main summary above the detail. Readers should be able to trace a headline result to its supporting build without finding the same calculation repeated elsewhere. Keep input retrieval, case selection and detailed business logic in the owning build/control area. Do not route forecast results through Assumptions before presenting them. Historical references used to set drivers and linked case/period displays remain allowed.
      
      **Check / Audit** tabs review source data and builds for completeness, consistency and reconciliation. They may calculate their own diagnostics, but do not own business calculations or feed assumptions, builds or outputs. Nothing outside the check/audit area should depend on its results.
      
      **Cover, if useful** gives a complex workbook a simple front page, especially for recurring or shared workflows. Include the company/project name or available logo, workbook title and relevant period or as-of date, with generous whitespace and restrained branding. Place it first. Keep analysis and methodology off the cover. Skip it for focused tasks or when the main output provides enough context.
      
      For complex workbooks, use a separate `ReadMe` only when source choices, joins, scoring or refresh steps need more explanation than nearby notes. Explain the method and material limitations without repeating outputs or giving a tab tour. Put it last. Multiple sources alone do not require one.
      
      Apply [Style guidance](style_guidelines.md) to these tab and section roles, so formatting helps readers distinguish the main answer, editable inputs and supporting calculations.
      
      ### Tab Names
      
      Use concise names that describe each tab's purpose, such as `Check` or `Audit` for a reconciliation tab. Preserve established names during unrelated edits. For new forecast work, use `Forecast review` for review checks, `Forecast variance` for comparisons with a prior forecast, or `Sensitivity` for assumption tests. Do not label these tabs or views `Movement` or `Forecast movement`.
      
      ### Tab Order & Progression
      
      For a new workbook or authorized redesign, start with one clear primary view that answers the task. Start with one tab, or two when the original source needs to stay separate, for focused tasks such as a department budget versus actuals report, a peer-company valuation comparison, a weekly marketing campaign report, an appointment-capacity tracker or a research measurement log with unit conversions. Preserve required source tabs and dependencies. Put the requested summary above the supporting detail and calculations. Add another tab only for a distinct source, calculation, reader or workflow need; do not create a separate tab for every role. Keep review commentary, refresh instructions and documentation beside the relevant work when they do not need a separate workflow.
      
      Keep separate schedules when the work requires them, such as revenue, payroll, depreciation and debt builds in a financial model. One or two tabs is a starting point for the examples above, not a limit on every workbook. Do not shrink text, hide necessary calculations or discard records to meet a tab count or fit one printed page. Preserve the supplied template and existing architecture during narrow edits.
      
      | Domain and task | Do: one output tab | Don't: create extra output/build tabs by default |
      | --- | --- | --- |
      | Finance / FP&A: one department's monthly budget versus actuals | On `Budget vs Actuals`, tab name `BvA`, show total spend and variance at the top, with category-level budget, actuals and variance calculations below. | Separate Summary, Dashboard, Scenarios and Assumptions tabs for this report. |
      | Financial modeling: peer-company valuation comparison from supplied data | On `Comparable Companies`, tab name `Comps`, show the requested multiple summaries at the top, with peer-company inputs and calculated multiples below. | A DCF, debt schedule or full three-statement model when the task only asks for comparable-company analysis. |
      | Marketing: weekly campaign spend and cost per lead | On `Campaigns`, show total spend, leads and overall cost per lead at the top, with campaign detail below. Calculate overall cost per lead from the matching totals. | One output tab per campaign, a duplicate dashboard or an attribution model that wasn't requested. |
      | Healthcare administration: appointment capacity by clinic | On `Appointments`, tab name `Appts`, show available slots, bookings and overall utilization at the top, with clinic and period detail below. Calculate overall utilization from the matching totals. | A separate dashboard, clinical alerts or a payroll schedule for an appointment report. |
      | Scientific research: measurement log with required unit conversions and a requested summary | On `Measurements`, show the requested results at the top, with original observations, units and required conversions below. | Separate Protocol, Processing, Calculations and Checks tabs, or statistical tests that the task does not require. |
      
      One output worksheet can contain several useful sections. Keep original sources and substantial builds separate when needed; do not create multiple output tabs for the same answer.
      
      For a file with multiple tabs, the physical left-to-right order is **Outputs → Builds → Inputs/Sources/Internal**, with a separate **Assumptions** control panel kept easy to reach, usually just after the primary output and before build tabs. Covers, key outputs (executive summary, financial statements, etc.) belong toward the left; working builds sit in the middle when needed; data, sources, inputs and internal documentation sit toward the right. A two-tab workbook has Output on the left and Input on the right. The logical calculation flow is Source/Input and Assumptions → Build → Output; a visible control panel may sit to the left of its builds. Do not confuse tab position with calculation sequence. Within a horizontal build, factors may feed intermediate results from left to right; preserve chronological period columns. Within a single worksheet, inputs and supporting calculations below can feed the main answer above. Preserve an intentional user/reference layout; do not reorganize a narrow edit to enforce this default.
      
      #### Checks and Audit
      
      Checks/Audit are terminal review areas and are not required for focused tasks. They read source/build evidence and may calculate or summarize their own diagnostics within that area. No formula outside a terminal check/audit area may use its results, directly or through helpers, names or dynamic references. This includes assumptions, business calculations, summaries, presented outputs, displayed statuses and output gates. Keep necessary input validation in the owning input/build logic; checks observe it independently. When separate tabs are useful, keep Checks/Audit and internal documentation toward the right. In complex workbooks, a divider such as `Internal >>` can group them with source data; follow [Style guidance](style_guidelines.md) for divider and child-tab colors. Preserve useful supplied controls and notes, but do not add separate tabs for a few lines.
      
      
      ### Build Structure and Formula Flow
      
      Arrange labeled rows and columns so a reader can follow starting data, assumptions, useful calculation steps, subtotals and results. Follow the physical layout above; the logical sequence of inputs to results does not require every build to run from top to bottom.
      
      - **Row progression:** make the useful business steps visible, such as quantity × rate, capacity used ÷ capacity available, or a balance plus its movements. Link the clean input and applicable assumption into their own labeled rows, then calculate the result on that build. Do not add trivial steps just to create more rows.
      - **Active assumptions:** select the active assumptions once in the control area and link each period's cells directly into the same build. Do not bypass the active row, repeat case selection across schedules, put a forecast inside Assumptions or maintain parallel case builds. Resolve a required comparison's calculation and refresh method as described in [Tab Types & Relationships](#tab-types--relationships).
      - **Historical reference:** Assumptions may link to historical ratios calculated from actuals in a build to help set forecast drivers. Trace the cells: this actuals-only reference must not create a feedback loop from the forecast into its own assumptions.
      - **Column progression:** keep comparable items, scenarios and periods aligned. Use the shared headers and controls described in [Anchoring](#anchoring) and [Dates and Time Periods](#dates-and-time-periods), rather than repeating them beside each calculation.
      - **Roll-forwards:** show opening balance, relevant movements and closing balance. Normally link each new period's opening balance to the prior period's closing balance, preserving the model's actual timing and conventions.
      - **Reuse:** keep one place that owns each calculation, then link matching results into summaries and useful output views. Apply the matching-input, period, unit, rounding and override conditions in [Formula Construction](#formula-construction).
      
      A tab that only repeats linked values from another tab or workbook is a red flag. Build tabs should perform useful calculations and show the steps. Output tabs should bring results together and calculate relevant subtotals or totals where needed. A useful output may link directly to completed build results without adding new calculations. Keep a linking-only tab when it serves a clear source, import or reporting need; otherwise, combine or remove it within the authorized scope. Do not invent calculations merely to justify a distinct reader view.
      
      ### Workbook Structure Examples
      
      | Example | Do | Don't |
      | --- | --- | --- |
      | A1. Simple action tracker | Use one `Actions` tab with owner, due date, status and the requested totals above the table. | Add Cover, Readme, Inputs, Dashboard and Checks tabs around a small task list. |
      | A2. Newly designed monthly activity report | Keep Month as a column in one activity table; use that table directly or add a linked summary tab to its left. | Copy the same layout into Jan, Feb and Mar tabs when separate monthly sheets are not required. |
      | A3. Compare several teams or campaigns | Keep the comparison in one table with a team/campaign field and the requested measures. | Create a separate nearly identical report tab for each team and make the reader assemble the comparison. |
      | A4. A few shared assumptions | Put a short labeled rate/assumption block to the left of the working calculation, or below the results on one worksheet. | Create Setup and Assumptions tabs for three cells, or duplicate editable copies of the same rate. |
      | A5. A requested scenario comparison | Group each driver's Active Selection and case inputs together. Keep one active build. Agree on any required comparison's calculation and refresh method, and label retained results accurately. | Maintain parallel case forecasts, omit the comparison or affected dependencies, link both cases to the active result, or use `TABLE` or snapshots as an ordinary shortcut. Do not add unneeded scenarios. Preserve explicitly required native sensitivity or [capture workflows](#circular-references-and-iterative-calculation). |
      | A6. Explain a one-page operating calculation | Put People needed at the top, the work/capacity calculation beneath it, and Requests and Minutes per request below. Let the lower inputs feed the answer above. | Scatter each step across a different tab, bury the answer at the bottom, or show only an unexplained staffing result. |
      | A7. Present an existing calculation | In a new multi-tab workbook, put Outputs on the left, Builds in the middle and Sources/Inputs on the right. Link the output to the completed build; on one worksheet, show that output above its build. Keep each editable control authoritative in one place; preserve an intentional front-end selector. | Put the primary output after internal source tabs, duplicate the same editable control in several places, create an unintended circular calculation, or rebuild the same calculation in the summary. |
      | A8. Reconcile a small import | Put an independent comparison near the relevant table. Use a Checks/Audit tab only if needed, and keep it a terminal reader of sources and builds. | Add a full control dashboard for one useful tie-out, or make the build, summary or output gate read a Checks/Audit result. |
      | A9. Keep source context usable | Document each source once alongside the relevant input data, following [Citation Requirements](#citation-requirements). Retain essential period/unit labels, required row-level source columns and intact source tabs. | Repeat filenames and source explanations across builds and outputs, hide essential context in cell notes, or create Sources, Notes, Methodology and Version History tabs for a one-off analysis with one source. |
      | A10. Summarize a long source table | Keep all required records intact and make the primary view compact. Use a separate source tab when it improves use or preserves the import. | Drop rows, hide needed calculations or make text tiny so all the evidence fits on one page. |
      | A11. A production plan with distinct schedules | Keep materials, line-capacity and staffing schedules separate when their inputs, time grains or update owners differ; place the primary output plan to the left of those builds, with supporting data/inputs farther right. | Merge incompatible schedules just to stay within two tabs, or repeat their calculations in the summary. |
      | A12. A narrow edit to an existing workbook | Change the requested cells and affected dependencies, preserving established tabs, native features and layout. | Normalize, merge, rename or remove existing tabs just because a new workbook could be simpler. |
      | A13. Several thin tabs around one calculation | For a new capacity plan, keep the input factors, meaningful work/capacity calculation and requested result together in one view or two useful tabs. A Build should contribute the steps shown in F13. | Create seven tabs that mostly repeat the same central range, with nominal Build tabs doing no distinct work. Putting that central calculation on Checks/Audit is also a dependency failure. |
      | A14. More than one output view | Keep an operator detail view and a manager summary when their fields, level of detail or workflow differ. Both may link to the same owning build, as in F14. | Copy the same table into Summary, Dashboard, Report and Executive tabs without a distinct reader need, or invent new calculations just to make each tab look different. |
      
      
      ## Formulas
      
      Apply these rules to newly added or edited formulas and their affected dependencies. Follow the user's preferences and supplied template; preserve unrelated formulas and layout during narrow edits. Design formulas to support the workbook structure above: the reader should be able to follow the inputs, useful calculation steps and final answer.
      
      ### Formula Construction
      
      - Use direct references, familiar functions and meaningful intermediate calculations. Follow [Build Structure and Formula Flow](#build-structure-and-formula-flow) to show the work; do not hide an entire build in one dense formula or add trivial helpers just to make formulas shorter.
      - Keep raw data, editable assumptions, mappings and business rules in labeled cells or tables. Mathematical, index and control constants may remain in formulas. Keep calculated results as formulas so they update with their inputs.
      - Fixed cutoffs or categories from the user's request can appear directly in formulas when result labels state the rule. For example, label `COUNTIFS(B2:B100,">1000")` as `Invoices over $1,000`, without adding an input cell for `1000`. Use one labeled input cell when the cutoff is user-adjustable or serves as a shared assumption across different calculations.
      - Calculate a shared result once and reuse it when the inputs, period, units, rounding and overrides match. Keep independent reconciliations independent.
      - Use consistent formulas across comparable rows and periods, while preserving intentional differences such as [historical versus forecast logic](domain_guidance/financial_models.md#periods-assumptions-and-scenarios), one-off adjustments and overrides.
      - Keep business calculations in the owning build and necessary input guards with their inputs or dependent build logic, following the [terminal Checks/Audit rule](#checks-and-audit). Do not invent business restrictions or wrap ordinary calculations in repeated workbook-wide validation gates. For example, use `=SUM(I11:I12)` for a valid total; do not add an `IF` that rejects a negative result unless the business rule requires it.
      
      ### Anchoring
      
      Use `$` to fix only the part of a reference that must stay in place when a formula is copied. Anchor shared **rows, columns or individual cells** so the workbook can reuse one period header, assumption block, item column or Case selector instead of repeating it beside every calculation.
      
      | Reference | What stays fixed | Useful pattern |
      | --- | --- | --- |
      | `C8` | Neither row nor column | A quantity that moves with the calculation when copied across or down. |
      | `C$4` | Row 4 | Read each column's period from one shared header row; copying across advances the period, copying down keeps that header. |
      | `$A8` | Column A | Read each row's item or category from one shared column; copying down advances the item, copying across keeps its label. |
      | `$B$3` | Cell B3 | Reuse one fixed conversion rate or Case selector throughout the applicable calculation. |
      
      For example, `=SUMIFS(Amount,Month,C$4,Item,$A8)` reads the period above and the item at the left. Copied one column right it uses `D$4`; copied one row down it uses `$A9`. The aligned named ranges represent the source columns; they do not require named ranges in the delivered workbook.
      
      A period-specific assumption should move with its period: `=C8*C$3` becomes `=D8*D$3` when copied across. A single assumption shared by every period should stay fixed: `=C8*$B$3` becomes `=D8*$B$3`. Choose between them from the model's meaning, not by adding `$` everywhere. Use keyed lookups when source and destination orders differ; anchoring cannot make mismatched row positions equivalent. Quote cross-sheet names, for example `='Build'!E14`.
      
      ### Dates and Time Periods
      
      - When calculations depend on a reporting date, use the date specified by the task or source. Use TODAY() only when calculations should update with the current date. Use a fixed reporting date when results should remain tied to a particular date. Label any assumed date. Preserve source deadlines and flag conflicts with derived deadlines.
      - Review the template's calendar, period layout and source grain before building formulas. Use real dates where the source supports them, with number formats for display; do not invent a missing reporting year. Derive period filters and labels from the shared header rather than hardcoding months in individual formulas.
      - For a new `Week of` label, use the week's first business day as the underlying date: Monday by default, moved forward for holidays only when a holiday calendar is supplied. Follow an explicit source/template week convention. Do not invent holidays or relabel a week-ending date as a week start.
      - When several time scales are needed and the template does not prescribe a layout, place the broader summaries to the left and finer detail to the right: **Annual | Quarterly | Monthly | Weekly**. Include only the time scales needed for the task. Keep periods chronological from left to right within each group; use the supplied fiscal calendar and week convention.
      - Separate different time scales with narrow, blank, unfilled spacer columns; do not extend formatting down the entire column. Do not add a spacer merely between actual and forecast months in one continuous schedule. Align matching period columns across Assumptions, builds and summaries where practical. When recent actuals help set drivers, include that historical reference on Assumptions in the same period column as the build, followed by the matching forecast periods. Within a continuous schedule, use one shared period header rather than repeating identical date rows above every subsection. Keep it visible when useful; separate tables with different column meanings may need their own headers, and print titles can repeat headers on printed pages.
      - Match each period to its own assumptions and data. Roll detail into summaries using the right calculation: sum additive amounts, use the appropriate ending balance for stocks, and calculate ratios or weighted averages from the relevant components. Do not sum monthly percentages or double-count weeks that cross month boundaries.
      
      For a monthly summary of daily dates, with `C4` holding the first day of the month and aligned source ranges, use `=SUMIFS(Amount,Date,">="&C$4,Date,"<"&EDATE(C$4,1),Item,$A8)`. The next-month exclusive upper bound includes the full last day, including timestamps. Equality to `C$4` is appropriate only when the source already stores that same monthly key.
      
      ### Choosing Formulas and Excel Tools
      
      - **Totals and products:** use `SUM` over the relevant detail for total rows. Use `PRODUCT` for a result built by multiplying a range of numeric factors, or direct multiplication for a simple two-cell calculation. Use `SUMPRODUCT` for a sum of matching quantity × rate pairs or a weighted calculation. Keep ranges aligned and bounded; do not include both subtotals and their detail. Check required factors first: `PRODUCT` ignores blank/text cells in a referenced range, which can make missing inputs look like a valid result.
      - **Conditional counts, sums and averages:** prefer `COUNTIFS`, `SUMIFS` and `AVERAGEIFS` for new formulas, even with one criterion, so another condition can be added consistently. Avoid choosing `COUNTIF`, `SUMIF` or `AVERAGEIF` for new work by default; preserve a valid existing/template convention during a narrow edit. This preference does not prohibit an ordinary `IF` condition.
      - **Lookups:** `INDEX/MATCH`, `VLOOKUP` and `XLOOKUP` are all useful. Follow the user's preference and the workbook's established approach where it works. Make exact versus approximate matching intentional, handle missing keys explicitly and confirm whether duplicate keys should be rejected, matched once or aggregated. Do not substitute a first-match lookup for a required sum.
      - **Conditional logic:** use a short `IF` for a simple choice. Nested `IF` formulas are appropriate when they express necessary, understandable logic, including advanced Finance calculations. For a long list of categories or editable rules, prefer a mapping table or labeled steps. Preserve rule order, boundaries, gaps and the unmatched case; do not replace useful business logic merely to reduce nesting.
      - **Formula choices to avoid:** do not introduce `LET`, array/spill formulas, `MAP`, `REDUCE` or `LAMBDA`. Use familiar formulas and labeled intermediate steps. Normal range arguments in functions such as `SUMIFS` and `SUMPRODUCT` remain appropriate, as do the lookup, `INDIRECT`, `OFFSET` and `CHOOSE` patterns below. Preserve required existing/template behavior and do not rewrite unrelated formulas during a narrow edit. Formula length alone is not the test: the reader must be able to understand and extend the calculation.
      - **Sensitivity analysis:** use a native What-If Data Table only for an explicitly requested native sensitivity analysis or required existing/template behavior, when supported. Do not introduce `TABLE` into an ordinary forecast or case comparison, or manufacture a second varying input with a metric selector. Excel supports one or two varying inputs; the current Artifact Tool supports only two-variable tables, with both input cells on the table’s worksheet. Read [Data Tables](artifact_tool_docs/DATA_TABLES.md) before creating one. Two inputs test one output across their combinations; use separate tables for additional outputs. If the requested native design is unsupported, explain the limitation before agreeing on a formula-based design or change-input/recalculate/restore process. Label captured results and their refresh method. Ordinary case comparisons follow the single-build and comparison boundary above.
      
      An Excel Table, PivotTable and What-If Data Table are different features. Check the chosen tool and destination's support. If a requested native feature cannot be created or preserved, explain the limitation before substituting a formula or static result. Keep API setup and feature-specific execution details in the relevant tool reference.
      
      ### Scalable Formulas and Brief Explanations
      
      Use the patterns below when they make recurring updates easier without hiding the calculation. Choose the simplest approach that supports the actual update workflow, not just the current snapshot.
      - **Assumption and Case selection:** prefer one numeric Case selector with labeled case names and `CHOOSE` or `OFFSET` to select the active assumptions. `INDEX/MATCH` or `XLOOKUP` remain valid when they fit the layout. In each driver group, put Active Selection above its case inputs, sharing the same period header. For example, with Case in B3 and two case values in I22:I23, active I21 can be `=CHOOSE($B$3,I22,I23)`; the matching build input is simply `='Assumptions'!I21`. Anchor and validate the selector. Do not repeat the choice in the build or maintain a second editable copy of the drivers. The simple CHOOSE example assumes validated numeric case inputs. Otherwise, test the selected source value before a reference can turn a blank into zero. Preserve a valid zero. A missing unselected case must not block the active case. In an agreed comparison, mark only the affected case and dependent deltas unavailable. Keep necessary validation local to the driver and reuse it. OFFSET and INDIRECT are volatile, so keep references bounded and consider recalculation cost.
      - **New monthly source tabs:** if the workflow receives a separate tab in the same format each month, a visible month-to-tab registry and bounded `INDIRECT` references can support new periods without rewriting the reference pattern. Register the new tab and extend the summary periods or bounded ranges when needed. Validate the expected layout, tab names and source coverage; quote and escape sheet names correctly. For a new workflow without that constraint, one source table with a Month column may be simpler.
      - **Explain recurring updates:** when a less familiar formula materially improves the workbook, add a short explanation near its control or in the existing guide: why it helps, what the user can change and how to extend it safely. For example: “Add the new month tab in the same layout and register its name in Setup. Extend the summary period and ranges if needed; the formulas keep the same reference pattern.” Keep this brief; do not add comments to every formula or create a new instruction tab for one note.
      
      ### Missing Inputs, Errors and Overrides
      
      - Do not invent missing source data or substitute a different metric. If required data is absent, leave the result unavailable and state the specific missing input beside its data or setting and briefly in the response. For a rate, preserve the requested numerator, denominator, population and period; do not substitute another available denominator.
      - Distinguish a real zero from missing data, an unavailable result and something that is not applicable. Use `"n.a."`, a deliberate `""` blank, or an exposed error according to the user's preference and the calculation's meaning. Right-align `n.a.` and similar placeholders when they sit among numeric results; do not turn them into numeric zero for appearance.
      - `IFERROR` can be useful for a deliberate, understood fallback, but must not hide unexpected failures. Prefer testing the expected condition directly, or `IFNA`/a lookup's not-found result when only a missing match is expected. Do not blanket-wrap formulas in `IFERROR(...,0)` or `IFERROR(...,"")` to make broken references and bad inputs disappear. Text `"n.a."` and the `#N/A` error are different; choose intentionally and ensure downstream formulas handle the result correctly.
      - Guards such as `ISNUMBER` must not turn a failed prerequisite into a healthy zero or an understated issue count. Keep unexpected failures visible in the affected results, even when an intermediate formula returns text or a blank instead of an error.
      - Handle necessary validation in the input/build that owns it, affecting only the relevant outputs. A SUMIFS result of zero does not prove matching records exist; retain a source-coverage test when no match must remain blank or unavailable. Keep the issue visible without spreading the same long guard through every summary formula or pulling a global status from Checks/Audit.
      - A matched lookup key does not prove its value is populated. Check required source values before a lookup or reference can turn a blank into zero; preserve a permitted numeric zero.
      - Add manual overrides only when the task, template or established workflow needs them. Otherwise, calculate directly from the relevant drivers; do not add an optional override row to every result.
      - Preserve deliberate zero overrides, blanks, one-off adjustments and rounding. A blank optional override may mean “use the base”; a zero override may mean “use zero.” Do not treat those as the same condition.
      
      ### Circular References and Iterative Calculation
      
      Avoid unintended circular references. Use intentional circular logic only when the requested model needs it and the selected tool and target engine support it. Document the loop and its purpose; preserve or deliberately configure iteration, maximum iterations and maximum change. Verify convergence after representative input changes and save/reopen. Do not silently enable iteration, change application-wide settings, or treat cached values, a successful export or an error-free scan as proof. If calculation or setting preservation cannot be verified, report the limitation and use a verified workflow or a mathematically equivalent non-circular approach within scope. Keep Checks/Audit outside the loop.
      
      An explicit/template case-capture workflow may use a self-retaining `IF` in an output area to store a selected case's result while the same model calculates the other cases. This is a snapshot, not a live recalculation of every case; assumptions and business calculations must not depend on it. Define initialization and capture/refresh steps, show the captured case and stale-state warning, and verify each case is captured and retained correctly in the intended engine. Convergence alone does not prove capture correctness. Do not introduce this pattern as a default scenario comparison.
      
      Present case results as a compact `Case comparison`, with each case named above comparable metric rows and period columns. Keep capture/refresh instructions secondary and label saved snapshots clearly; a new label or layout does not make them live.
      
      ### Formula Examples
      
      These examples assume the inputs, ranges and units described. Named ranges stand for labeled source ranges, not a requirement to add names. Preserve the task's missing-data policy and material rounding.
      
      | Example | Do | Don't |
      | --- | --- | --- |
      | F1. Reuse an editable assumption | With one fixed conversion rate in B3, use `=C8*$B$3`. With a different rate in each period of row 3, use `=C8*C$3` and fill across. | Hardcode the rate in every formula, or let a shared rate drift to a neighboring cell when copied. |
      | F2. Show a build on one worksheet | Put Requests in B10 and Minutes per request in B9; calculate Work minutes in B8 as `=PRODUCT(B9:B10)`. With positive Available minutes per person in B7, put People needed in B6 as `=B8/B7`, with required whole-person rounding. All factors must be present and numeric. | Hide input retrieval, unit conversion and staffing logic inside one unexplained output, or treat a missing factor as zero workload. |
      | F3. Reuse the matching subtotal | If B12 is the eligible-volume subtotal for the required period, calculate `=B12*$B$3`. | Re-sum the detail in every output, or reuse a subtotal with different eligibility, units, period or rounding. |
      | F4. Link a period rollforward | Link this month's Beginning inventory to the prior month's Ending inventory; calculate Ending as Beginning + Receipts − Usage. | Rebuild cumulative history from the first month in every period when the prior ending balance already represents the same quantity. |
      | F5. Resolve a shared lookup once | With unique validated keys and matched ranges, put the rate in D8 with `=INDEX('Rates'!$C$5:$C$12,MATCH($A8,'Rates'!$A$5:$A$12,0))`; reuse D8 for that same rate. An established VLOOKUP or XLOOKUP pattern is also valid. | Repeat the same lookup in each output, silently select an ambiguous duplicate, or add a helper for an already simple one-use expression. |
      | F6. Replace a long category decision tree | Keep the category-to-owner mapping in a table; with unique keys, use `=XLOOKUP($A8,Categories,Owners,"Unmapped",0)`. | Repeat a long category `IF` chain in every row, or remove necessary conditional model logic merely because it uses nested IFs. |
      | F7. Preserve rule boundaries | For supplied bands `0 ≤ x < 100`, `100 ≤ x < 500`, and `x ≥ 500`, preserve those boundaries and test the thresholds and values on either side. | Turn `<100` into `≤100`, reorder overlapping tests, fill an intentional gap or invent a default category. |
      | F8. Guard the expected exception | With validated numeric B8 and C8 and a not-applicable policy for a zero denominator, use `=IF(C8=0,"n.a.",B8/C8)`. A deliberate blank may be appropriate under a different display policy. | Use `IFERROR(...,0)` so missing data or a broken reference appears to be a real zero rate. |
      | F9. Preserve a zero override | With base B8 and validated optional override C8, use `=IF(C8="",B8,C8)`. | Use `=IF(C8=0,B8,C8)` and erase a valid zero override, or overwrite the base to apply an adjustment. |
      | F10. Fill using shared headers and labels | Use `=SUMIFS(Amount,Month,C$4,Item,$A8)` for matching monthly keys. Row 4 supplies periods across the table; column A supplies items down it. Use the date-bounds pattern above for daily source dates. | Repeat the same date header in every subsection, hardcode January across the year, or assume differently ordered source tabs have matching row positions. |
      | F11. Choose the aggregate that matches the math | Use `=SUM(C8:C11)` for a total, `=PRODUCT(C8:C10)` for three required numeric factors, or `=SUMPRODUCT(B8:B11,C8:C11)` for matching quantity × rate pairs. Use SUMIFS for an ordinary conditional sum. | Replace these with a custom array pipeline, double-count subtotal rows, or let PRODUCT silently skip a missing required factor. |
      | F12. Keep checks independent and one-way | If a Checks tab is warranted, compare the build with an independent source control there, such as `='Build'!E14-'Source'!D20`. | Use `='Checks'!C8` in a build, summary or output gate, compare a total with itself, or treat a cached PASS as a newly executed check. |
      | F13. Show progression within a build | For A13's capacity plan, use numeric Runs in C8 and kWh per run in D8 to calculate Energy needed in E8 as `=C8*D8`. With positive Available kWh in F8 for the same period, calculate Capacity share in G8 as `=E8/F8`. | Label a linked copy “Build,” hide all factors in one long formula, or add relay tabs without useful work. |
      | F14. Share a result across useful views | For A14's distinct output views, let both read the owning result, such as `='Build'!E14`, and present the detail their readers need. | Recompute the same result in every output, or copy the same table into several tabs without a distinct reader or workflow need. |
      
      
      ## Writing Quality and Authored Content
      Apply these defaults to text you write, including titles, labels and messages returned by formulas. User instructions and preferences, reference/template conventions and domain guidance take precedence, in that order. For edits, do not change unrelated content outside of the user's request and follow the workbook’s existing writing style.
      
      - Write for the intended audience. Never include internal file paths, authoring commentary, planning notes, or requester instructions in the artifact unless explicitly requested. Do not repeat audience or style directives such as “executive-friendly” in headings, content, or comments.
        - Omit: `Discussion support only. This workbook does not make final rating or promotion decisions.` just because the user asked for a workbook for discussion.
        - Omit: `Supports discussion and consistency checks. Human reviewers remain responsible.` unless that limitation is explicitly required.
      
      - Include text only when it helps the reader understand the data or use the workbook. Keep clear text unchanged. Rewrite useful text that is unclear. Delete unnecessary text instead of replacing it with a cleaner version of the same filler.
      
      - Use concise, plain-language titles and labels. Name the specific subject, issue or action and avoid internal jargon and vague status labels. Preserve what each label measures, including the population, period, units, comparison, and uncertainty. Do not shorten a label by removing a distinction the reader needs.
        - Good: `Weekly metrics`. Bad: `Follow the weekly trends`
        - Use `Metric` for a general metric column and `Revenue driver` for a revenue assumption explanation. Avoid invented labels such as `Planning measure`, `Movement explanation` or `Planning basis`. Retain specific labels when they add necessary meaning.
        - Bad: `Requisition blockers`. Good: `Hiring requests awaiting approval` when approval is the issue.
        - Bad: `Two-band rating movement`. Choose a descriptive, clear phrase that represents the underlying event, e.g.:
          - Promotion: `Promoted by two job levels`
          - Rating change: `Performance rating increased by two levels`
        - Good: `Monthly results`. Bad: `Decision-ready monthly impact analysis`
        - Good: `Income and household assumptions`. Bad: `Same paycheck. Different purchasing power.`
        - Use `Retained employees` only for employees who remained over a defined period. Otherwise, name the population counted, such as `Total employees` or `Employees reviewed`.
      
      - Avoid decorative bullets, icons, emoji, arrows and pipe-delimited titles. Omit filler suffixes; keep terms such as `review`, `analysis` or `dashboard` when they identify the content.
        - Bad: `$ in USD • monthly • forecast`
        - Good: `Monthly forecast (USD)`
      
      - Prefer direct, specific human wording. Avoid slogans, buzzwords, invented terminology, vague framing and formulaic claims.
        - Good (when supported by the data): `Most revenue growth comes from data centers.` Bad: `Data centers are doing the heavy lifting.`
        - Good: `Contributions decreased`. Bad: `Contributions waned`
        - Good: `Revenue metrics`. Bad: `Strategic Value Drivers`
        - Bad formulaic phrasing: `The tool not only saves time, but also transforms how teams collaborate.` or `Faster, smarter, and more intuitive.`
        - Bad: `While remote work offers flexibility, it also presents unique challenges.` (synthetic balance without a real tradeoff)
        - Bad: `Operating evidence improved`. Operating evidence is unclear and not a common term used.
      
      - Avoid AI-like sentence constructions. Use direct sentences with clear meaning and avoid vague explanations and forced contrasts. Prefer periods between sentences. Do not use semicolons, pipes, bullets, or dashes to assemble several labels into a slogan.
        - Semicolons and vague explanations: Use `Travel demand and employment fell from Jan to Feb.`, not `Travel demand and employment fell from Jan to Feb; persistent behavior shifts are shaping the path back.`.
        - Passive voice when active is clearer e.g. Use `The team approved the proposal.` not `The proposal was approved by the team.`
        - Contrast slogans like `It’s not X, it’s Y`: For a title, use `Humidity exposure over time` not `Humidity is an exposure trajectory, not a setpoint.`
        - Unnecessary em-dashes: Bad: `Purpose: isolate what changed – and what deliberately stayed in place – under Osaka Prefecture’s Red Stage emergency response.`
      
      - Keep wording factual, parseable and supported by the workbook.
        - Good: `Transit use is 79% of pre-pandemic levels.`
        - Bad: `79% Transit use back to pre-pandemic`
      
      - Omit repeated information, obvious purpose statements and generic disclaimers. Subtitles are optional. State critical definitions and material assumptions once beside the relevant data or setting. Preserve task-required limits and warnings, such as a review supporting discussion rather than making final personnel decisions.
      
      - Do not include motivational wording or self-assessment. Omit decorative badges and self-evaluation banners. Preserve task-required business statuses, risk flags, uncertainty labels and specific warnings as ordinary data. Do not invent scoring systems or confidence scales merely to decorate the workbook.
        - Omit: `This workbook is source-backed and ready for review`.
      
      - For checks and logic, be specific:
        - Bad: `Signal integrity: BLOCKED`. Good: `Missing input: forecast rate` (a specific functional warning)
      
      - For a requested workflow, provide an obvious editable field for required human input, separate from original source notes. Short calculated statuses or actions should reflect all required prerequisites. Do not imply completion while another required action is still open.
      
      
      ## Workflows
      Required:
      - `workflows/edit_workflows.md` for existing files/follow-ups.
      - `workflows/create_workflows.md` for new files
      
      ## Resources
      Read the following BEFORE starting the task:
      
      Required:
      - `artifact_tool_docs/API_QUICK_START.md` for `artifact_tool` JS API documentation. Read entirely.
      - `style_guidelines.md` for formatting.
      
      As applicable:
      - `references/template-elicitation.md`: if user has not provided a template, reference, or visual direction.
      - `references/image-references.md`: if a reference image or screenshot is provided.
      - `references/read_only_qna.md`: for Q&/audits
      - `features/charts.md`: for creating or editing charts.
      
      <a id="domain-requirements"></a>
      
      ## Role and Domain Guidance
      Before authoring, identify the user's **task/function**, **role**, **audience** and **industry** separately, then read the relevant guides below. Apply the professional conventions of the work being done; a role or industry label alone does not determine the workbook's structure or formatting.
      - Use function guidance for the work being done. Financial forecasts, budgets, cash models and valuations use Finance guidance in any industry.
      - Add industry requirements only when they affect definitions, units, source handling or the workflow. A healthcare company's financial forecast uses Finance guidance; an appointment tracker does not inherit financial-model structure or colors.
      - Use the user's role and audience to choose useful detail, terminology and outputs, and to resolve ambiguity in the task. Do not apply Finance conventions to an unrelated task just because the user works in Finance. Explicit instructions and templates retain precedence; relevant domain conventions override generic defaults.
      
      Guides:
      - Finance, corporate finance and FP&A, financial modeling, valuation and investment banking: `domain_guidance/financial_models.md`. Read the relevant financial requirements below the shared structure, formula and style rules.
      - Healthcare: `domain_guidance/healthcare.md`
      - Marketing and advertising: `domain_guidance/marketing_advertising.md`
      - Scientific research: `domain_guidance/scientific_research.md`
      
      ## Create and Edits
      For any task that requires modifying or creating a workbook:
      
      ### Data Formatting Rules
      - Store numbers, percentages, currency, and dates as typed spreadsheet values, not preformatted strings. Use text only for true identifiers such as ZIP codes, account IDs, SKUs, or labels.
      - Use Excel-invariant number/date format codes, not locale-specific display strings. Generic numeric examples include `#,##0`, `#,##0.0`, `0.0%`, `0.00%`, `"$"#,##0`, `"$"#,##0.00`. Preserve source dates and unrelated existing formats.
      - Percentages: Follow the domain or reference's precision. Otherwise, use 1 decimal for most analytical cells, 0 decimals for dashboard outputs, and 2 decimals where small rate differences matter.
      - Do not swap `.` and `,` in format codes to mimic locale separators; separators are controlled by spreadsheet/render locale. Use `0.0%`, not `0,0%`, and `#,##0`, not `#.##0`.
      - Choose the appropriate format for readability. Match precision to meaning: counts use `#,##0`; rates usually use `0.0%` or `0.00%`; currency uses whole units unless cents matter.
      
      - For dates in data columns, default to a short date format appropriate to the workbook's language/location, such as `mm/dd/yy` for the US. Follow explicit user preferences and reference/template or domain conventions.
      
      Keep underlying dates numeric and sortable. A display format does not change the period represented or authorize aggregation. Fit the final display so dates do not truncate or show `####`.
      
      ### Verification Rules
      Use Artifact Tool to verify requested features and results within the authorized changes and their affected dependencies. Match coverage to the scope, complexity and risk. Report unrelated pre-existing defects without repairing them. Reuse checks for unchanged content and keep authoring-only tests out of the delivered workbook.
      
      After completing all edits, call `workbook.recalculate()` once before the final checks below and export. If you make further edits, recalculate again before repeating affected checks and exporting.
      ```js
      workbook.recalculate();
      ```
      
      1. Inspect labels, values and formulas in key ranges:
      ```js
      const check = await workbook.inspect({
        kind: "table",
        range: "Dashboard!A1:H20",
        include: "values,formulas",
        tableMaxRows: 20,
        tableMaxCols: 12,
      });
      console.log(check.ndjson);
      ```
      
      Check what each source row represents, units, reporting periods, and numerators and denominators for rates. Spot-check representative metrics against source data or an independent calculation. Trace headline results through the build to inputs, including named and dynamic references. Confirm the build does useful calculations and does not depend on terminal Checks/Audit. When cases are used, trace each period to its active assumptions. Summary should link to finished results without repeating the build or routing results through Assumptions. An actuals-only historical calibration reference is allowed.
      
      Check formula copying across and down at first, middle and later rows/periods. When the workflow promises extensions, test the next record, period or requested case. Keep notes and overrides tied to stable record IDs after supported sorts or refreshes. Reconcile key totals to independent source controls using the right period aggregation. Apply tolerances appropriate to the units and precision, but compare identifiers, counts and categories exactly. Investigate double-counting or conflicting data and fix confirmed errors within scope.
      
      2. Scan formula errors:
      ```js
      const errors = await workbook.inspect({
        kind: "match",
        searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
        options: { useRegex: true, maxResults: 300 },
        summary: "final formula error scan",
      });
      console.log(errors.ndjson);
      ```
      
      Check wrong or shifted references and unintended cycles as well as reported errors. Distinguish deliberate missing-data markers from unexpected failures. Trace unavailable results and zero issue counts through their prerequisites: a failed detail calculation must not disappear into a healthy zero or an understated summary.
      
      3. Verify applicable recalculation in the intended engine. Test representative input changes and boundaries in a disposable copy or restore every temporary edit before delivery. Include blank versus zero, missing/duplicate keys, period cutoffs, overrides and rounding. For cases, change the selector and a later-period driver. Confirm the same build and linked outputs update while actuals remain unchanged. A blank unselected input must not block a valid active case; selecting that case must expose the missing input. Verify any agreed comparison refresh and stale-state behavior separately. Report any engine checks that could not be performed.
      
      For workflows, check that required human inputs have editable fields and that completion guidance accounts for every prerequisite. Complete one prerequisite while leaving another open and confirm the remaining action stays visible. For input-driven rankings and action lists, change an input that should alter the order or included records and verify the list updates. Verify affected charts, status text, validation and conditional formatting react to edits. A saved value, static matrix or unchanged PASS cell is not recalculation proof.
      
      4. Render sheets/ranges to verify visual output. Skip only when the rendered view and its data/formula dependencies are unchanged:
      ```js
      const blob = await workbook.render({ sheetName: "Sheet1", range: "A1:H20", scale: 2 });
      ```
      For creation or broad authorized restructuring, visually review every sheet. For a narrow edit, review the changed view and affected dependencies, then compare all tabs with the source for unintended value, formula, object, validation or style changes. Do not repeatedly render unchanged tabs; investigate any scope-preservation failure.
      
      Inspect at normal zoom with cells unselected. Fix blank/broken charts, low-contrast text, unreadable fonts, clipped headers/numbers, `####`, awkward wrapping, truncated chart labels, default blank sheets and content outside the working area. Check effective cell/chart fonts, fitted row heights and widths, pane boundaries and conditional-format ranges. Logical titles and labels should appear once with a clear layout. Valid check values should stay neutral, with errors and missing inputs visibly distinct. Do not shrink content to force a fit.
      
      Keep output compact: avoid arbitrary formula-count checks, assumptions about file storage and huge NDJSON dumps.
      
      5. Export:
      ```js
      await fs.mkdir(outputDir, { recursive: true });
      const output = await SpreadsheetFile.exportXlsx(workbook);
      await output.save(`${outputDir}/output.xlsx`);
      ```
      
      6. Inspect the saved file when an affected feature or export concern requires it. Verify requested or preserved native features in the intended engine, including any explicitly required Data Table input/output behavior. Check iteration and capture behavior separately when used.
      
      Finalize only after successful export and the applicable checks. Report what was performed and any remaining limitations. Formula text, a preview and a successful export do not establish native-application behavior.
      - Do not export extra `.xlsx` variants unless asked.
      
      ### Citation Requirements
      These are defaults for new workbooks: user instructions, reference/template conventions and domain guidance take precedence. For edits, follow the workbook’s existing citation practices.
      - Cite real sources when they exist.
      - Keep citations and sources in one place: an existing input tab (sources or data tab) or in the correct input section in a tab, alongside the input data.
      - There are two ways to cite a source: 
        1. (Preferred) Inline in the input tab when the tab exists.
          - If there are multiple unique sources (different pages/lines don't count), inline them in an adjacent cell at the table's end, with one column as a buffer, when a table exists
          - If there is a single source, just have a single cell above the data, left aligned.
        2. (Fallback) Cell note, not a comment/thread, with the citation
          Only do this for hardcoded inputs not on a separate input tab, such as an input area on a build sheet. For adjacent cells in the same row or column that come from the same source, do not add duplicate cell notes. Never add citation notes to titles or headers.
      - If there is no clear place for sources, return sources in chat. Do not add a tab just for citations.
      - Citation format should follow best practice for domain, default to `(Source: Company 10-K, FY2026, Page 20, Revenue Note, [URL LINK])`
      - Do not add citations, comments or notes to cover/presentation tabs or output regions unless requested. On a mixed-use sheet, citations may sit beside the input data, outside the output region.
      - When comments are requested, keep them succinct, minimal and easy to read.
      - Do not add a different annotation type to a cell that already has one. Update an existing note/comment/thread rather than layering another system over it.
      - Do not add cell comments unless the user requests them. Preserve existing annotations.
      
      ## Completion Criteria
      ### Criteria for Question / Read only requests
      - Answer from the available workbook context. Do not edit or overwrite unless the user asks for a workbook change.
      
      ### Criteria for all create and edit requests
      Complete only when:
      - Content is populated, addresses the user's request, and formulas compute, with no obvious formula errors in key scanned ranges (including bad-reference, off-by-one or circular errors).
      - `.xlsx` saved to `outputs/<unique_thread_id>/`.
      - Visual verification passes: organized, legible layout matches requested style or default/existing edit baseline; all important numbers/callouts are visible; numbers, text, charts and content are unclipped without awkward wrapping.
      - Required controls, charts, panes and requested features exist.
      
      ## Error Recovery
      On first tool or API error:
      1. Read error text.
      2. Consult the selected workflow's targeted help or schema discovery only if needed.
      3. Retry with minimal patch (not full rewrite).
      4. Continue from existing workbook state.
      
      Do not loop indefinitely on similar failures.
      
      ## Final response
      
      ### Final response citations
      
      Place :codex-file-citation{...} inline in prose without wrapping it in backticks or a code block, not in a trailing list. Use `purpose="source"` for Q&A/no-op and `purpose="output"` for create/edit.
      
      - [HARD REQUIREMENT] Create/edit: cite each final workbook exactly once with a plain output citation. Summarize representative changes; do not cite every sheet/range or add a separate filename, path, or Markdown link. Example: `Created :codex-file-citation{path="/abs/path/inventory.xlsx" purpose="output"} with formula-driven status and a summary.`
      - Q&A: cite whole-workbook claims plainly; otherwise use the narrowest reliable `sheet` + `range` (the exact cell for a discrete value). Cite discontiguous cells separately. For objects, use `sheet` + exact inspected `object_id`; add `object_kind`/`label` only when useful. Never cite a sheet alone or guess locators.
      - Calculations: cite only distinct inputs, drivers, formulas, or results the answer needs.
      
      :codex-file-citation{path="/abs/path/book.xlsx" purpose="source" artifact_kind="workbook" sheet="Revenue Model" range="C27"}
      
      Never cite intermediates unless asked.
      
      ### Final response suggested followups
      
      - After successfully creating, editing, or analyzing an artifact, finish your final response with 3 useful next actions tailored to the artifact and the user's goal. Completing the requested work is not a reason to skip these actions: they help the user continue from the result. Do not perform the actions unless the user chooses one.
      - Each action must be a distinct, concrete request the user could send next. Do not repeat completed work or invent filler. Omit the list if the user declines suggestions, the requested work fails, or no genuinely useful next action remains.
      - Present each action as an unescaped Markdown list item using this exact syntax: `- :codex-followup[Short action]{prompt="Complete request for that action"}`.
      
      ## Comment Author
      - If the authenticated/user profile or env context provides a user display name, use it as the threaded comment display name unless the user requests another name. Default to `User`.
      
      ## Source, PDF, and Attachment Processing
      - For attachment references, include only the file/section/table details needed to locate supporting data. Do not paste large PDF excerpts unless requested.
      - Bundled Python libraries available in the bundled runtime environment for extraction/analysis include `pandas`, `numpy`, `pypdf`, `python-docx`, and `reportlab`. You may read/extract in separate scripts if needed.
      - Bundled JS libraries available for document/PDF work include `docx`, `pdf-lib`, and `pdfjs-dist`.

## Activity

    $ /bin/zsh -lc "sed -n '180,453p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/SKILL.md && sed -n '1,200p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/workflows/edit_workflows.md && sed -n '1,240p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/artifact_tool_docs/API_QUICK_START.md && sed -n '241,520p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/artifact_tool_docs/API_QUICK_START.md && sed -n '1,180p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/style_guidelines.md && sed -n '1,160p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/domain_guidance/scientific_research.md"
    status: Completed · exit 0
      ## Scientific Research Guidance
      
      Use for research observations, experiments, lab measurements, surveys, statistical analysis and reproducibility tasks. Follow [Domain Requirements](../SKILL.md#domain-requirements) for other functions: a research organization's financial forecast uses Finance guidance, not research-data formatting solely because of its industry.
      
      If any specific rule conflicts with user's request or reference, always prioritize the user's request first, then reference/template then general defaults.
      Use [Style guidance](../style_guidelines.md) for shared formatting; apply the data-table requirements below to the relevant research records and interfaces.
      
      For read-only questions, inspect relevant source records, calculations, definitions, units, periods and protocols without modifying/exporting, changing inputs, adding helper fields/checks or refreshing sources. Report gaps and failed checks rather than repairing them. Authoring defaults apply only to requested creation or edits; preserve original source records and narrow-edit scope.
      
      ### Tab structure & naming
      
      - Keep raw observations intact in a clearly identified flat table, with one variable per column and one observation per row. Raw, processed and results are distinct roles, not a mandatory number of worksheets.
      - Put cleaning or transformations in separate columns/regions or a processed-data sheet when needed; never overwrite original measurements. Choose separate sheets for substantive transformations, refresh boundaries, reproducibility or review needs, and preserve the requested source layout.
      - Document cleaning steps and protocol in an existing appropriate region or a dedicated sheet when their extent warrants it. Add Calculations or Results sheets only for a distinct analytical or reader purpose, not to expand a simple raw-data export.
      
      ### Formatting
      
      For raw/processed data tables consumed by analytical tools:
      
      - Each column should contain one type of data (with units in the header, not mixed into the cells) and each row one record.
      - Avoid merging cells or creating multi-row headers that can complicate data import into analysis tools.
      - Do not use formatting (color, bold, italics) as the sole means to encode information, since analytical software may not recognize it. When flags are needed, use a labeled value column rather than a cell comment or color alone.
      - Layout should be plain and data-focused: for instance, list any comments or notes in a separate column rather than as Excel cell comments or text boxes. This makes the data more machine-readable.
      
      ### Formula practices
      
      - In scientific spreadsheets, complex data analysis is often done outside Excel, but when using formulas, prioritize transparency and accuracy.
      - For requested randomization or simulation, document the method and inputs and preserve the protocol's reproducibility requirements. Follow [Choosing Formulas and Excel Tools](../SKILL.md#choosing-formulas-and-excel-tools) for formula choices.
      - Avoid unrequested circular references. If a required protocol or reference uses iteration, follow [Circular References and Iterative Calculation](../SKILL.md#circular-references-and-iterative-calculation) and document its reproducibility implications.
      - Show meaningful calculation steps under [Build Structure and Formula Flow](../SKILL.md#build-structure-and-formula-flow), without adding helpers for trivial expressions. Cross-check consequential calculations where possible and report limitations. Preserve the recorded protocol, source units and original measurements; distinguish flags, missing observations, simulation/randomness and assumptions without silently changing the analysis design.

## Activity

    $ /bin/zsh -lc "sed -n '1,179p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/SKILL.md"
    status: Completed · exit 0
      ---
      name: "Spreadsheets"
      description: "Use skill when user requests to create, modify, analyze, visualize, or work with spreadsheet files (`.xlsx`, `.xls`, `.csv`, `.tsv`) or Google Sheets with formulas, formatting, charts, tables, and recalculation. Do not use for live controlling Microsoft Excel app or a live Excel session."
      ---
      
      # Spreadsheets skill
      Read entirely for spreadsheet creation, editing, analysis, or visualization.
      
      ## Decision Boundary
      - Google Sheets targeted outputs also require `routing/google_sheets.md`. Otherwise, author local files with artifact tool.
      
      ## Important Instructions
      - For new workbooks or authorized redesigns, plan the simplest correct workbook that meets the task, audience, actual data and domain. If formulas become hard to read, first reconsider whether the workbook’s structure, layout, or logic is overcomplicated before simplifying individual formulas. Remove unnecessary or duplicated logic while preserving calculation correctness, required business relationships, and financial reconciliation
      - Instruction precedence for workbook content, layout, and formatting is: user request > reference/template > domain defaults/conventions > general defaults.
      
      ## Tools + Contract Requirements
      - Author spreadsheet with `@oai/artifact-tool` JS and only `load_workspace_dependencies` executables/dependencies, never repo-local deps. If unavailable, check `~/.cache/codex-runtimes/codex-primary-runtime/dependencies/`. Never modify dependency directories.
      - In a writable, conversation-specific or tmp directory, create a `node_modules` symlink or Windows junction to the loader `node_modules`.
      - Prefer to patch/rerun one `.mjs` builder. No heredocs or duplicate builders.
      - Use the provided API reference for supported syntax. Its examples do not set workbook structure, formatting or formula defaults. Do not inspect package internals or prototypes. If blocked, run at most one targeted `workbook.help("<api_or_feature>")` query.
      - No `openpyxl`, `xlsxwriter`, or `pandas.ExcelWriter` authoring unless asked, or  `@oai/artifact-tool` is unavailable.
      - Analyze with JS/formulas, else bundled Python (libraries) and JSON/CSV intermediates; other libraries only for missing capabilities.
      - Use `update_plan` for complex work.
      - In your final response, omit builders, previews, or other support files unless requested.
      - Immediately before the first create/edit authoring command, run `mark_artifact_operation_started.mjs` successfully exactly once using the command below. Do not run it for read-only work. For edits, replace `create` with `edit`; adjust the expected count and output format to match the requested outputs.
        ```bash
        node container_tools/mark_artifact_operation_started.mjs --operation-kind create --expected-output-count 1 --output-format xlsx
        ```
      
      ## Spreadsheet (Workbook) Complexity: Workbook Structure & Formulas
      
      Keep the workbook simple, especially for focused tasks. A focused task produces a simple analysis, report or tracker for a specific question or workflow. It needs one main output, supported by the necessary inputs and calculations. “Focused” describes the scope of the task, not the number of source records.
      
      Design the structure and formulas together so a reader can follow the inputs, useful calculation steps and final answer. Put summaries and main outputs first, show the work behind them, and avoid tabs or formulas that only repeat finished results. Keep separate schedules and output views when they serve distinct needs. Preserve required detail, the supplied template and the requested edit scope.
      
      ## Workbook Structure
      
      ### Tab Types & Relationships
      
      Tab types describe the role each part of the workbook plays. They do not require separate tabs. A simple workbook can combine inputs, assumptions, builds and outputs in clearly labeled sections on one worksheet.
      
      **Inputs/Sources and Assumptions feed Builds; Builds calculate results and feed Outputs.** These relationships describe how calculations flow, not the physical tab order. The same rules apply when roles share a tab.
      
      **Input / Sources** contain the data the workbook starts from. Keep dedicated raw source or Actuals areas intact, with original values and source meaning separate from prepared calculations. Cleaning, mapping and source summaries may have their own labeled areas with clear provenance. Put business calculations, including historical calibration from actuals, in the build. Raw source data does not read results back from downstream areas.
      
      **Assumptions** hold the editable drivers and controls used by the builds. When cases are needed, keep one authoritative Case selector on Cover or Assumptions. Group each driver with its `Active Selection` row first, followed by its labeled case inputs, such as Base and Downside, sharing the same period columns. Prefer these driver groups to separate whole-case blocks for new designs. The build links directly to each period's active input. Preserve a supplied layout during narrow edits, and do not add cases or a separate tab when the task does not need them.
      
      Changing the Case selector updates the active forecast assumptions for each period. The same build keeps linking to those active cells and recalculates with the selected values. Outputs update from the build results while historical actuals remain unchanged.
      
      When cases are used, display the selected case on each worksheet by linking to the authoritative selector. Keep only one editable selector; distinguish source actuals and separately labeled comparison cases from the active forecast.
      
      In historical periods, the active assumption row may link to ratios or other measures calculated from actuals in a build. Show that history once, aligned with the build's historical period columns, to help the user set forecast assumptions. The forecast active row selects the chosen case's assumptions and feeds the build. Forecast results must not feed back into the assumptions driving that same forecast. Historical calibration is a business calculation, not a terminal Check/Audit result.
      
      **Build** tabs pull source inputs and assumptions to combine historical analysis, current results and/or a forecast. Bring the relevant inputs and applicable assumptions into clearly labeled rows or columns, then calculate the results on the build. Keep periods aligned and chronological. Show meaningful steps, subtotals and totals so readers can follow the logic—for example, headcount and compensation driving personnel cost, or revenue less COGS producing gross profit. Each step should do useful work. Do not hide the whole calculation in one dense formula or make the build merely repeat finished results from elsewhere.
      
      For a simple calculation, a small labeled assumption block can sit beside it. For a larger build, link important drivers from their control area and show the useful calculation steps. Use one set of forecast schedules driven by the active assumptions, organized by the business sequence, such as revenue, headcount, vendors and cash. Do not mirror the Assumptions grid, add Case columns or parallel named-case forecasts, or apply the selector only to finished results.
      
      A requested case comparison still needs each case's correctly evaluated results. If the requested simultaneous current results cannot be produced with the supported single-build design, explain the limitation and agree on the calculation or refresh method before building the comparison. Do not omit it, link both cases to the active result, or silently substitute snapshots, `TABLE`, arrays, dense formulas or a hidden second build. Preserve explicit user/template requirements and the separately authorized native-feature and capture workflows below.
      
      **Output / Summary** tabs consolidate the builds and tell the main story. These might be named “Overview,” “Summary,” “Exec Summary” or “Dashboard,” depending on the task. Bring across finished build results, show how matching totals roll into higher-level totals and put the main summary above the detail. Readers should be able to trace a headline result to its supporting build without finding the same calculation repeated elsewhere. Keep input retrieval, case selection and detailed business logic in the owning build/control area. Do not route forecast results through Assumptions before presenting them. Historical references used to set drivers and linked case/period displays remain allowed.
      
      **Check / Audit** tabs review source data and builds for completeness, consistency and reconciliation. They may calculate their own diagnostics, but do not own business calculations or feed assumptions, builds or outputs. Nothing outside the check/audit area should depend on its results.
      
      **Cover, if useful** gives a complex workbook a simple front page, especially for recurring or shared workflows. Include the company/project name or available logo, workbook title and relevant period or as-of date, with generous whitespace and restrained branding. Place it first. Keep analysis and methodology off the cover. Skip it for focused tasks or when the main output provides enough context.
      
      For complex workbooks, use a separate `ReadMe` only when source choices, joins, scoring or refresh steps need more explanation than nearby notes. Explain the method and material limitations without repeating outputs or giving a tab tour. Put it last. Multiple sources alone do not require one.
      
      Apply [Style guidance](style_guidelines.md) to these tab and section roles, so formatting helps readers distinguish the main answer, editable inputs and supporting calculations.
      
      ### Tab Names
      
      Use concise names that describe each tab's purpose, such as `Check` or `Audit` for a reconciliation tab. Preserve established names during unrelated edits. For new forecast work, use `Forecast review` for review checks, `Forecast variance` for comparisons with a prior forecast, or `Sensitivity` for assumption tests. Do not label these tabs or views `Movement` or `Forecast movement`.
      
      ### Tab Order & Progression
      
      For a new workbook or authorized redesign, start with one clear primary view that answers the task. Start with one tab, or two when the original source needs to stay separate, for focused tasks such as a department budget versus actuals report, a peer-company valuation comparison, a weekly marketing campaign report, an appointment-capacity tracker or a research measurement log with unit conversions. Preserve required source tabs and dependencies. Put the requested summary above the supporting detail and calculations. Add another tab only for a distinct source, calculation, reader or workflow need; do not create a separate tab for every role. Keep review commentary, refresh instructions and documentation beside the relevant work when they do not need a separate workflow.
      
      Keep separate schedules when the work requires them, such as revenue, payroll, depreciation and debt builds in a financial model. One or two tabs is a starting point for the examples above, not a limit on every workbook. Do not shrink text, hide necessary calculations or discard records to meet a tab count or fit one printed page. Preserve the supplied template and existing architecture during narrow edits.
      
      | Domain and task | Do: one output tab | Don't: create extra output/build tabs by default |
      | --- | --- | --- |
      | Finance / FP&A: one department's monthly budget versus actuals | On `Budget vs Actuals`, tab name `BvA`, show total spend and variance at the top, with category-level budget, actuals and variance calculations below. | Separate Summary, Dashboard, Scenarios and Assumptions tabs for this report. |
      | Financial modeling: peer-company valuation comparison from supplied data | On `Comparable Companies`, tab name `Comps`, show the requested multiple summaries at the top, with peer-company inputs and calculated multiples below. | A DCF, debt schedule or full three-statement model when the task only asks for comparable-company analysis. |
      | Marketing: weekly campaign spend and cost per lead | On `Campaigns`, show total spend, leads and overall cost per lead at the top, with campaign detail below. Calculate overall cost per lead from the matching totals. | One output tab per campaign, a duplicate dashboard or an attribution model that wasn't requested. |
      | Healthcare administration: appointment capacity by clinic | On `Appointments`, tab name `Appts`, show available slots, bookings and overall utilization at the top, with clinic and period detail below. Calculate overall utilization from the matching totals. | A separate dashboard, clinical alerts or a payroll schedule for an appointment report. |
      | Scientific research: measurement log with required unit conversions and a requested summary | On `Measurements`, show the requested results at the top, with original observations, units and required conversions below. | Separate Protocol, Processing, Calculations and Checks tabs, or statistical tests that the task does not require. |
      
      One output worksheet can contain several useful sections. Keep original sources and substantial builds separate when needed; do not create multiple output tabs for the same answer.
      
      For a file with multiple tabs, the physical left-to-right order is **Outputs → Builds → Inputs/Sources/Internal**, with a separate **Assumptions** control panel kept easy to reach, usually just after the primary output and before build tabs. Covers, key outputs (executive summary, financial statements, etc.) belong toward the left; working builds sit in the middle when needed; data, sources, inputs and internal documentation sit toward the right. A two-tab workbook has Output on the left and Input on the right. The logical calculation flow is Source/Input and Assumptions → Build → Output; a visible control panel may sit to the left of its builds. Do not confuse tab position with calculation sequence. Within a horizontal build, factors may feed intermediate results from left to right; preserve chronological period columns. Within a single worksheet, inputs and supporting calculations below can feed the main answer above. Preserve an intentional user/reference layout; do not reorganize a narrow edit to enforce this default.
      
      #### Checks and Audit
      
      Checks/Audit are terminal review areas and are not required for focused tasks. They read source/build evidence and may calculate or summarize their own diagnostics within that area. No formula outside a terminal check/audit area may use its results, directly or through helpers, names or dynamic references. This includes assumptions, business calculations, summaries, presented outputs, displayed statuses and output gates. Keep necessary input validation in the owning input/build logic; checks observe it independently. When separate tabs are useful, keep Checks/Audit and internal documentation toward the right. In complex workbooks, a divider such as `Internal >>` can group them with source data; follow [Style guidance](style_guidelines.md) for divider and child-tab colors. Preserve useful supplied controls and notes, but do not add separate tabs for a few lines.
      
      
      ### Build Structure and Formula Flow
      
      Arrange labeled rows and columns so a reader can follow starting data, assumptions, useful calculation steps, subtotals and results. Follow the physical layout above; the logical sequence of inputs to results does not require every build to run from top to bottom.
      
      - **Row progression:** make the useful business steps visible, such as quantity × rate, capacity used ÷ capacity available, or a balance plus its movements. Link the clean input and applicable assumption into their own labeled rows, then calculate the result on that build. Do not add trivial steps just to create more rows.
      - **Active assumptions:** select the active assumptions once in the control area and link each period's cells directly into the same build. Do not bypass the active row, repeat case selection across schedules, put a forecast inside Assumptions or maintain parallel case builds. Resolve a required comparison's calculation and refresh method as described in [Tab Types & Relationships](#tab-types--relationships).
      - **Historical reference:** Assumptions may link to historical ratios calculated from actuals in a build to help set forecast drivers. Trace the cells: this actuals-only reference must not create a feedback loop from the forecast into its own assumptions.
      - **Column progression:** keep comparable items, scenarios and periods aligned. Use the shared headers and controls described in [Anchoring](#anchoring) and [Dates and Time Periods](#dates-and-time-periods), rather than repeating them beside each calculation.
      - **Roll-forwards:** show opening balance, relevant movements and closing balance. Normally link each new period's opening balance to the prior period's closing balance, preserving the model's actual timing and conventions.
      - **Reuse:** keep one place that owns each calculation, then link matching results into summaries and useful output views. Apply the matching-input, period, unit, rounding and override conditions in [Formula Construction](#formula-construction).
      
      A tab that only repeats linked values from another tab or workbook is a red flag. Build tabs should perform useful calculations and show the steps. Output tabs should bring results together and calculate relevant subtotals or totals where needed. A useful output may link directly to completed build results without adding new calculations. Keep a linking-only tab when it serves a clear source, import or reporting need; otherwise, combine or remove it within the authorized scope. Do not invent calculations merely to justify a distinct reader view.
      
      ### Workbook Structure Examples
      
      | Example | Do | Don't |
      | --- | --- | --- |
      | A1. Simple action tracker | Use one `Actions` tab with owner, due date, status and the requested totals above the table. | Add Cover, Readme, Inputs, Dashboard and Checks tabs around a small task list. |
      | A2. Newly designed monthly activity report | Keep Month as a column in one activity table; use that table directly or add a linked summary tab to its left. | Copy the same layout into Jan, Feb and Mar tabs when separate monthly sheets are not required. |
      | A3. Compare several teams or campaigns | Keep the comparison in one table with a team/campaign field and the requested measures. | Create a separate nearly identical report tab for each team and make the reader assemble the comparison. |
      | A4. A few shared assumptions | Put a short labeled rate/assumption block to the left of the working calculation, or below the results on one worksheet. | Create Setup and Assumptions tabs for three cells, or duplicate editable copies of the same rate. |
      | A5. A requested scenario comparison | Group each driver's Active Selection and case inputs together. Keep one active build. Agree on any required comparison's calculation and refresh method, and label retained results accurately. | Maintain parallel case forecasts, omit the comparison or affected dependencies, link both cases to the active result, or use `TABLE` or snapshots as an ordinary shortcut. Do not add unneeded scenarios. Preserve explicitly required native sensitivity or [capture workflows](#circular-references-and-iterative-calculation). |
      | A6. Explain a one-page operating calculation | Put People needed at the top, the work/capacity calculation beneath it, and Requests and Minutes per request below. Let the lower inputs feed the answer above. | Scatter each step across a different tab, bury the answer at the bottom, or show only an unexplained staffing result. |
      | A7. Present an existing calculation | In a new multi-tab workbook, put Outputs on the left, Builds in the middle and Sources/Inputs on the right. Link the output to the completed build; on one worksheet, show that output above its build. Keep each editable control authoritative in one place; preserve an intentional front-end selector. | Put the primary output after internal source tabs, duplicate the same editable control in several places, create an unintended circular calculation, or rebuild the same calculation in the summary. |
      | A8. Reconcile a small import | Put an independent comparison near the relevant table. Use a Checks/Audit tab only if needed, and keep it a terminal reader of sources and builds. | Add a full control dashboard for one useful tie-out, or make the build, summary or output gate read a Checks/Audit result. |
      | A9. Keep source context usable | Document each source once alongside the relevant input data, following [Citation Requirements](#citation-requirements). Retain essential period/unit labels, required row-level source columns and intact source tabs. | Repeat filenames and source explanations across builds and outputs, hide essential context in cell notes, or create Sources, Notes, Methodology and Version History tabs for a one-off analysis with one source. |
      | A10. Summarize a long source table | Keep all required records intact and make the primary view compact. Use a separate source tab when it improves use or preserves the import. | Drop rows, hide needed calculations or make text tiny so all the evidence fits on one page. |
      | A11. A production plan with distinct schedules | Keep materials, line-capacity and staffing schedules separate when their inputs, time grains or update owners differ; place the primary output plan to the left of those builds, with supporting data/inputs farther right. | Merge incompatible schedules just to stay within two tabs, or repeat their calculations in the summary. |
      | A12. A narrow edit to an existing workbook | Change the requested cells and affected dependencies, preserving established tabs, native features and layout. | Normalize, merge, rename or remove existing tabs just because a new workbook could be simpler. |
      | A13. Several thin tabs around one calculation | For a new capacity plan, keep the input factors, meaningful work/capacity calculation and requested result together in one view or two useful tabs. A Build should contribute the steps shown in F13. | Create seven tabs that mostly repeat the same central range, with nominal Build tabs doing no distinct work. Putting that central calculation on Checks/Audit is also a dependency failure. |
      | A14. More than one output view | Keep an operator detail view and a manager summary when their fields, level of detail or workflow differ. Both may link to the same owning build, as in F14. | Copy the same table into Summary, Dashboard, Report and Executive tabs without a distinct reader need, or invent new calculations just to make each tab look different. |
      
      
      ## Formulas
      
      Apply these rules to newly added or edited formulas and their affected dependencies. Follow the user's preferences and supplied template; preserve unrelated formulas and layout during narrow edits. Design formulas to support the workbook structure above: the reader should be able to follow the inputs, useful calculation steps and final answer.
      
      ### Formula Construction
      
      - Use direct references, familiar functions and meaningful intermediate calculations. Follow [Build Structure and Formula Flow](#build-structure-and-formula-flow) to show the work; do not hide an entire build in one dense formula or add trivial helpers just to make formulas shorter.
      - Keep raw data, editable assumptions, mappings and business rules in labeled cells or tables. Mathematical, index and control constants may remain in formulas. Keep calculated results as formulas so they update with their inputs.
      - Fixed cutoffs or categories from the user's request can appear directly in formulas when result labels state the rule. For example, label `COUNTIFS(B2:B100,">1000")` as `Invoices over $1,000`, without adding an input cell for `1000`. Use one labeled input cell when the cutoff is user-adjustable or serves as a shared assumption across different calculations.
      - Calculate a shared result once and reuse it when the inputs, period, units, rounding and overrides match. Keep independent reconciliations independent.
      - Use consistent formulas across comparable rows and periods, while preserving intentional differences such as [historical versus forecast logic](domain_guidance/financial_models.md#periods-assumptions-and-scenarios), one-off adjustments and overrides.
      - Keep business calculations in the owning build and necessary input guards with their inputs or dependent build logic, following the [terminal Checks/Audit rule](#checks-and-audit). Do not invent business restrictions or wrap ordinary calculations in repeated workbook-wide validation gates. For example, use `=SUM(I11:I12)` for a valid total; do not add an `IF` that rejects a negative result unless the business rule requires it.
      
      ### Anchoring
      
      Use `$` to fix only the part of a reference that must stay in place when a formula is copied. Anchor shared **rows, columns or individual cells** so the workbook can reuse one period header, assumption block, item column or Case selector instead of repeating it beside every calculation.
      
      | Reference | What stays fixed | Useful pattern |
      | --- | --- | --- |
      | `C8` | Neither row nor column | A quantity that moves with the calculation when copied across or down. |
      | `C$4` | Row 4 | Read each column's period from one shared header row; copying across advances the period, copying down keeps that header. |
      | `$A8` | Column A | Read each row's item or category from one shared column; copying down advances the item, copying across keeps its label. |
      | `$B$3` | Cell B3 | Reuse one fixed conversion rate or Case selector throughout the applicable calculation. |
      
      For example, `=SUMIFS(Amount,Month,C$4,Item,$A8)` reads the period above and the item at the left. Copied one column right it uses `D$4`; copied one row down it uses `$A9`. The aligned named ranges represent the source columns; they do not require named ranges in the delivered workbook.
      
      A period-specific assumption should move with its period: `=C8*C$3` becomes `=D8*D$3` when copied across. A single assumption shared by every period should stay fixed: `=C8*$B$3` becomes `=D8*$B$3`. Choose between them from the model's meaning, not by adding `$` everywhere. Use keyed lookups when source and destination orders differ; anchoring cannot make mismatched row positions equivalent. Quote cross-sheet names, for example `='Build'!E14`.
      
      ### Dates and Time Periods
      
      - When calculations depend on a reporting date, use the date specified by the task or source. Use TODAY() only when calculations should update with the current date. Use a fixed reporting date when results should remain tied to a particular date. Label any assumed date. Preserve source deadlines and flag conflicts with derived deadlines.
      - Review the template's calendar, period layout and source grain before building formulas. Use real dates where the source supports them, with number formats for display; do not invent a missing reporting year. Derive period filters and labels from the shared header rather than hardcoding months in individual formulas.
      - For a new `Week of` label, use the week's first business day as the underlying date: Monday by default, moved forward for holidays only when a holiday calendar is supplied. Follow an explicit source/template week convention. Do not invent holidays or relabel a week-ending date as a week start.
      - When several time scales are needed and the template does not prescribe a layout, place the broader summaries to the left and finer detail to the right: **Annual | Quarterly | Monthly | Weekly**. Include only the time scales needed for the task. Keep periods chronological from left to right within each group; use the supplied fiscal calendar and week convention.
      - Separate different time scales with narrow, blank, unfilled spacer columns; do not extend formatting down the entire column. Do not add a spacer merely between actual and forecast months in one continuous schedule. Align matching period columns across Assumptions, builds and summaries where practical. When recent actuals help set drivers, include that historical reference on Assumptions in the same period column as the build, followed by the matching forecast periods. Within a continuous schedule, use one shared period header rather than repeating identical date rows above every subsection. Keep it visible when useful; separate tables with different column meanings may need their own headers, and print titles can repeat headers on printed pages.
      - Match each period to its own assumptions and data. Roll detail into summaries using the right calculation: sum additive amounts, use the appropriate ending balance for stocks, and calculate ratios or weighted averages from the relevant components. Do not sum monthly percentages or double-count weeks that cross month boundaries.
      
      For a monthly summary of daily dates, with `C4` holding the first day of the month and aligned source ranges, use `=SUMIFS(Amount,Date,">="&C$4,Date,"<"&EDATE(C$4,1),Item,$A8)`. The next-month exclusive upper bound includes the full last day, including timestamps. Equality to `C$4` is appropriate only when the source already stores that same monthly key.
      
      ### Choosing Formulas and Excel Tools
      
      - **Totals and products:** use `SUM` over the relevant detail for total rows. Use `PRODUCT` for a result built by multiplying a range of numeric factors, or direct multiplication for a simple two-cell calculation. Use `SUMPRODUCT` for a sum of matching quantity × rate pairs or a weighted calculation. Keep ranges aligned and bounded; do not include both subtotals and their detail. Check required factors first: `PRODUCT` ignores blank/text cells in a referenced range, which can make missing inputs look like a valid result.
      - **Conditional counts, sums and averages:** prefer `COUNTIFS`, `SUMIFS` and `AVERAGEIFS` for new formulas, even with one criterion, so another condition can be added consistently. Avoid choosing `COUNTIF`, `SUMIF` or `AVERAGEIF` for new work by default; preserve a valid existing/template convention during a narrow edit. This preference does not prohibit an ordinary `IF` condition.
      - **Lookups:** `INDEX/MATCH`, `VLOOKUP` and `XLOOKUP` are all useful. Follow the user's preference and the workbook's established approach where it works. Make exact versus approximate matching intentional, handle missing keys explicitly and confirm whether duplicate keys should be rejected, matched once or aggregated. Do not substitute a first-match lookup for a required sum.
      - **Conditional logic:** use a short `IF` for a simple choice. Nested `IF` formulas are appropriate when they express necessary, understandable logic, including advanced Finance calculations. For a long list of categories or editable rules, prefer a mapping table or labeled steps. Preserve rule order, boundaries, gaps and the unmatched case; do not replace useful business logic merely to reduce nesting.
      - **Formula choices to avoid:** do not introduce `LET`, array/spill formulas, `MAP`, `REDUCE` or `LAMBDA`. Use familiar formulas and labeled intermediate steps. Normal range arguments in functions such as `SUMIFS` and `SUMPRODUCT` remain appropriate, as do the lookup, `INDIRECT`, `OFFSET` and `CHOOSE` patterns below. Preserve required existing/template behavior and do not rewrite unrelated formulas during a narrow edit. Formula length alone is not the test: the reader must be able to understand and extend the calculation.
      - **Sensitivity analysis:** use a native What-If Data Table only for an explicitly requested native sensitivity analysis or required existing/template behavior, when supported. Do not introduce `TABLE` into an ordinary forecast or case comparison, or manufacture a second varying input with a metric selector. Excel supports one or two varying inputs; the current Artifact Tool supports only two-variable tables, with both input cells on the table’s worksheet. Read [Data Tables](artifact_tool_docs/DATA_TABLES.md) before creating one. Two inputs test one output across their combinations; use separate tables for additional outputs. If the requested native design is unsupported, explain the limitation before agreeing on a formula-based design or change-input/recalculate/restore process. Label captured results and their refresh method. Ordinary case comparisons follow the single-build and comparison boundary above.
      
      An Excel Table, PivotTable and What-If Data Table are different features. Check the chosen tool and destination's support. If a requested native feature cannot be created or preserved, explain the limitation before substituting a formula or static result. Keep API setup and feature-specific execution details in the relevant tool reference.

## Activity

    $ /bin/zsh -lc "sed -n '1,220p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/artifact_tool_docs/API_QUICK_START.md"
    status: Completed · exit 0
      # Using artifact_tool APIs (JavaScript)
      
      Library version: 2.8.58+
      
      ## Required imports, setup and exports
      ```js
      import fs from "node:fs/promises";
      import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";
      
      // To import existing workbook
      const input = await FileBlob.load("path/to/input.xlsx");
      const workbook = await SpreadsheetFile.importXlsx(input);
      
      // To create a new workbook and add a sheet to it
      const workbook = Workbook.create();
      const sheet = workbook.worksheets.add("Inputs");
      
      // To export
      await fs.mkdir(outputDir, { recursive: true });
      const output = await SpreadsheetFile.exportXlsx(workbook);
      await output.save(`${outputDir}/output.xlsx`);
      ```
      
      Import CSV text directly when the source or intermediate data is CSV:
      ```js
      const csvText = await fs.readFile("path/to/input.csv", "utf8");
      const workbook = await Workbook.fromCSV(csvText, { sheetName: "Sheet1" });
      ```
      Prefer `Workbook.fromCSV(...)` over hand-parsing CSV rows; clean or analyze CSV with Python/Node first only when needed.
      CSV fields import as strings. Convert intended numeric/date columns before calculations; number formatting alone does not convert text to numbers.
      
      
      ## Build Patterns
      - Prefer block writes (`range.values`, `range.formulas`) over per-cell loops. Normally match the matrix shape to the target range (e.g. "D4:M4" → 1×10). To intentionally expand a larger matrix from an anchor, target a single cell or use range.write(matrix).
      - `range.values = [[value]]` repeats that value across the range; range.formulas does not broadcast a single formula. For merged ranges, write to the top-left cell or `mergedRange.values = [[value]]` where `mergedRange` is a single merged range.
      - Seed scalar formulas once, then `fillDown()` / `fillRight()`. For dynamic-array formulas (like `SEQUENCE`, `UNIQUE`, `FILTER`, `SORT`, `VSTACK`, `HSTACK`), write only the anchor cell and let the result spill after.
      - Use `range.displayFormulas` plus `range.formulaInfos` when you need to understand a spill child or a data-table output cell.
      - Setting cell values or formulas automatically recalculates dependent formulas; no manual recalculation is needed after ordinary edits, including batches (exception: creating data tables). Call `workbook.recalculate()` once after all edits, before final verification and export. If you make further edits, recalculate again before rechecking and exporting.
      - Prefer real `Date` objects for sortable/charted/formula date columns.
      - Number and date formats must be applied explicitly (for example `yyyy-mm-dd`).
      - Use JSON-serializable values for non-Date cells: `string | number | boolean | null`.
      - If a cell is intended to display literal text that begins with `=`, write it as a value prefixed with a single quote (for example `'=B2*C2`). This includes formula descriptions, validation examples, and labels; do not write these cells through `range.formulas`.
      - Create every worksheet referenced by formulas before writing any cross-sheet formulas.
      - Verify with `await workbook.inspect(...)`; use `workbook.help(...)` only when the quick surface below is insufficient.
      - `render` can be used to examine an existing workbook visually and for visual verifications.
      
      ## Conventions
      - Use camelCase API names and option keys.
      - Cell/range addressing: A1 notation (`sheet.getRange("A1:C10")`).
      - Drawing anchors (`sheet.charts`, `sheet.shapes`, `sheet.images`): 0-based `{ row, col }`.
      - Drawing offsets/extents use pixels (`rowOffsetPx`, `colOffsetPx`, `widthPx`, `heightPx`).
      
      ## API Discovery Policy (Strict)
      - Use this quick API surface first.
      - Use `workbook.help(...)` only when the supplied public documentation leaves a required operation unclear. Start with one bounded exact feature/path lookup, such as `range.dataValidation` or `chart.series.add`.
      - If that lookup returns no useful match, one bounded reformulation is allowed. Stop after those two attempts; do not repeat similar queries, inspect package internals/prototypes/nearby tests, or invent enum values and setters. Use a documented equivalent that preserves the task.
      
      ## Supported Formulas
      - Look up formula syntax with `fx.<formula>`, e.g. `workbook.help("fx.PMT", { include: "index,examples,notes", maxChars: 3000 })`. A help entry does not guarantee working calculation or Excel export.
      - To browse a family of formulas, use `fx.*` with a category regex. Useful categories: `financial`, `math-trig`, `statistical`, `lookup-reference`, `logical`, `text`, `date-time`, `information`, `engineering`, `database`.
      - For intent-based lookup, use a short natural query plus a narrow `search` regex of likely functions.
      - Keep `maxChars` bounded; if results are noisy, narrow `search` rather than issuing many similar queries.
      
      ```
      console.log(workbook.help("fx.PMT", { include: "index,examples,notes" }).ndjson);
      console.log(workbook.help("fx.*", { search: "financial", include: "index,examples", maxChars: 4000 }).ndjson);
      console.log(workbook.help("lookup with fallback", { search: "XLOOKUP|INDEX|MATCH|IFERROR", include: "index,examples,notes", maxChars: 4000 }).ndjson);
      ```
      
      ### Known formula/export limitations (not exhaustive)
      If a formula fails, use a verified equivalent that preserves the intended result.
      
      Known issues:
      - Avoid `MAP`, `REDUCE`, `SCAN`, `MAKEARRAY`, `GROUPBY`, `PIVOTBY`. Use helper cells and supported scalar formulas;
      - Prefix `XLOOKUP`, `TEXTJOIN`, `MINIFS`, `MAXIFS`, `IFS`, and `RANK.EQ` with `_xlfn.`, including nested calls: e.g. `'=_xlfn.TEXTJOIN(", ",TRUE,B2:C2)'`.
      - If using `LET`, `LAMBDA`, `BYROW`, and `BYCOL`, prefix function names with `_xlfn.` and every LET/LAMBDA local-variable declaration and reference with `_xlpm.`. This is compatibility syntax, not guidance to introduce those formulas.
      - PivotTable APIs exist, but XLSX export is unreliable.
      - `COUNTIF` / `COUNTIFS` with an empty-string criterion can miss blank cells, even in bounded ranges. For unconditional blank counts, use `COUNTBLANK(range)`.
      
      
      ## Reading existing/imported workbooks
      - On existing/imported workbooks, get a compact summary via `inspect` to understand what already exists and where.
      - Prefer `inspect(...)` for workbook understanding and discovery across broad areas.
      - Prefer direct getters like `range.formulas` when you already know the target range and need the exact rectangular formula matrix.
      - If formula locations are unknown, prefer `inspect({ kind: "formula", ... })` over reading `range.formulas` across a very large area.
      - Prefer to set `maxChars`, `tableMaxRows`, `tableMaxCols`, and/or `maxResults` to prevent large dumps of data.
      - For suspicious or high-impact outputs, use `workbook.trace("Sheet!A1")` to audit the dependency tree from final output/check cell back to source cells. Trace output can be large, so summarize by depth/node count before logging.
      
      ### Inspect for workbook understanding
      - Compact summary:
      ```js
      await wb.inspect({
        kind: "workbook,sheet,table",
        maxChars: 6000,
        tableMaxRows: 6,
        tableMaxCols: 6,
        tableMaxCellChars: 80,
      });
      ```
      - Quick overview of sheet ids and names: `await wb.inspect({ kind: "sheet", include: "id,name" })`
      - Formula discovery in a targeted area: `await wb.inspect({ kind: "formula", sheetId: firstSheetName, range: "A1:Z30", maxChars: 2500, options: {maxResults:50} })`
      - Checking existing styles in a targeted area: `await wb.inspect({ kind: "computedStyle", sheetId: firstSheetName, range: "A1:E10", maxChars: 2500 })`
      - Common `kind` tokens: `workbook`, `sheet`, `table`, `region`, `match`, `formula`, `thread`, `computedStyle`, `definedName`, `drawing`
      - Inspects can also be used to zoom in on specific areas, especially for target edits:
      ```js
      await wb.inspect({
        kind: "region",
        sheetId: firstSheetName,
        range: "A1:Z30",
        maxChars: 2500,
      });
      ```
      - Inspect output may include JSON records with `"id"` values (for example `"ws/r5qsk5"`), which you can resolve back to workbook objects with `wb.resolve(...)`:
      - `wb.resolve("ws/...")` -> worksheet
      - `wb.resolve("th/...")` -> comment thread
      
      ## Known Gotchas (Do not repeat)
      - Do not set undocumented attributes on remote objects.
      - `Workbook.create()` starts with no sheets; add one before calling `getActiveWorksheet()`.
      - Create every worksheet referenced by formulas before writing cross-sheet formulas.
      - Prefer bounded formula ranges, e.g. `$A$6:$A$205`. Full-column references can be truncated to each column's populated extent: unequal extents can make `COUNTIFS` / `SUMIFS` return `#VALUE!`, and `ROWS` / `INDEX` can differ from Excel.
      - If export fails, isolate the cause by checkpoint-export after major blocks to isolate the cause: base sheets, values/formulas, formatting, conditional formatting, tables, charts/rendering. For charts, first simplify optional styling first: nested border configs, custom chart axis/series mutations, broad autofit/formatting, then nonessential drawings.
      
      ## Quick API Surface (High-Value + Common)
      
      ### Core workbook/file APIs
      - `import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool"`
      - `const workbook = Workbook.create()` to create an empty workbook
      - `const sheet = workbook.worksheets.add("Sheet1")` to add a sheet
      - `const workbook = await SpreadsheetFile.importXlsx(arrayBufferOrFileBlob)`
      - `const xlsx = await SpreadsheetFile.exportXlsx(workbook); await xlsx.save("output.xlsx")`
      - `const inspect = await workbook.inspect({ kind: "sheet", include: "id,name", sheetId, range: "A1:C10" })`
      - `const help = workbook.help("worksheet.getRange", { include: "index,examples" })`
      - Preferred: `const preview = await workbook.render({ sheetName: "Sheet1", autoCrop: "all", scale: 1, format: "png" })`
      - To get the bytes and/or save the blob to file:
      ```js
      const previewBytes = new Uint8Array(await preview.arrayBuffer());
      await fs.writeFile(`${outputDir}/preview.png`, previewBytes);
      ```
      - `const workbook = await Workbook.fromCSV(csvText, { sheetName: "Sheet1" })`
      - `await workbook.fromCSV(csvText, { sheetName: "ImportedData" })` requires an empty workbook; it does not append CSV to a populated workbook. Prefer static `Workbook.fromCSV(...)`.
      
      ### Worksheet selection/creation
      - `workbook.worksheets.add(name)`
      - `workbook.worksheets.getItem(name)`
      - `workbook.worksheets.getItemAt(index)`
      - `workbook.worksheets.getActiveWorksheet()` (only after at least one sheet exists)
      
      ### Worksheet operations
      - `sheet.getRange("A1:C10")`, `sheet.getRangeByIndexes(startRow, startCol, rowCount, colCount)`, `sheet.getCell(row, col)`
      - `sheet.getUsedRange(valuesOnly?)`
      - `sheet.freezePanes.freezeRows(rowCount)`, `sheet.freezePanes.freezeColumns(columnCount)`, `sheet.freezePanes.unfreeze()`
      - `sheet.tabColor = "#1F4E78"` sets the worksheet tab color; the getter returns a `Color` object.
      - `sheet.tables`, `sheet.charts`, `sheet.sparklineGroups` (`sheet.sparklines` alias), `sheet.shapes`, `sheet.images`
      - `sheet.showGridLines = false`
      - `sheet.dataTables`, `sheet.conditionalFormattings`, `sheet.dataValidations`
      - `sheet.deleteAllDrawings()` removes all drawings, including charts, shapes, and images.
      
      ### Range values/formulas
      - `const range = sheet.getRange("A1:C10")`
      - `range.values = [[...], ...]` (2D matrix of values).
      - `range.formulas = [["=..."], ...]`
      - `range.formulasR1C1 = [["=RC[-1]*2"]]`
      - To read: `range.values` / `range.formulas` / `range.displayFormulas` / `range.formulaInfos` (for spill/array formulas)
      - `range.write(matrixOrPayload)` (auto-sizes/spills from anchor as needed)
      - `range.writeValues(matrixOrRows)`
      - `range.fillDown()`, `range.fillRight()`
        - `sheet.getRange("D2").formulas = [["=..."]]`
        - `sheet.getRange("D2:D200").fillDown()`
      - `range.clear({ applyTo: "contents" | "formats" | "all" })` clears cell contents, formatting, or both; drawings remain.
      - `range.copyFrom(sourceRange, "values" | "formulas" | "all")`. Prefer matching shapes; a single-cell value source can broadcast across a larger destination.
      - `range.copyTo(destRange, "values" | "formulas" | "all")`
      - `range.offset(rowOffset, colOffset)`, `range.resize(rowCount, columnCount)`, `range.getCurrentRegion()`, `range.getRow(i)`, `range.getColumn(j)`
      - `range.getRangeByIndexes(startRow, startCol, rowCount, colCount)`, `range.getCell(row, col)` (relative to the range)
      
      ### Formatting
      - `range.format` supports `fill`, `font`, `numberFormat`, `borders`, alignments, `wrapText`
      - `range.format.verticalAlignment = "center"` maps to Excel Middle Align
      - `range.format.autofitColumns()`, `range.format.autofitRows()`
      - Excel unit sizing:  `range.format.columnWidth = 18`, `range.format.rowHeight = 24`
      - Pixel sizing: `range.format.columnWidthPx = 120`, `range.format.rowHeightPx = 24`
      - `range.setNumberFormat("yyyy-mm-dd")`
      - `range.format.numberFormat = [["0"], ["0.00"], ["@"]]`
      - Borders: There are two ways to set borders on a range (1) simple form (2) per edge form. Example:
      ```js
      // (1) Preferred simple form
      // `preset` can be "none" | "outside" | "inside" | "all" | "doubleBottom"
      // "outside" will just set borders on the outside edges of the range.
      // `style` are Excel/OpenXML-style names such as "thin", "medium", "thick", "dashed", and "dotted".
      range.format.borders = { preset: "all", style: "thin", color: "#D9D9D9" };
      
      // (2) Per-edge form. Use top/bottom/left/right, not edgeTop/edgeBottom/etc.
      // Format: {style?: string; color?: ColorConfig; weight?: number;}
      // Prefer setting `style` over `weight` unless you want granular control.
      range.format.borders = {
        insideHorizontal: { style: "thin", color: "#D9D9D9" },
        insideVertical: { style: "medium", color: "#D9D9D9" },
        top: { style: "thick", color: "#D9D9D9" },
        bottom: { style: "dashed", color: "#D9D9D9" },
        left: { style: "dotted", color: "#D9D9D9" },
        right: { style: "thin", color: "#D9D9D9" },
      };
      ```
      
      ### Data Validation
      - `range.dataValidation = { rule: { type: "list", formula1: "Categories!$A$2:$A$4" } }`
      - `range.dataValidation = { rule: { type: "list", values: ["Not Started", "In Progress"] } }`
      - `sheet.dataValidations.add({ range: "B2:B100", rule: { type: "whole", operator: "between", formula1: 1, formula2: 10 } })`
      
      ### Conditional formatting
      - Use `range.conditionalFormats.add(ruleType, ConditionalFormatConfig);`.
      - Use `range.conditionalFormats.add(ruleType, {operator, formula, format});`. Choose ruleType, operator, color, and style strings from the inline types below.
      ```
      type ConditionalFormatRuleType =
        | "cellIs" | "CellValue" | "Custom" | "expression"
        | "colorScale" | "dataBar" | "iconSet"
        | "containsText" | "notContainsText" | "beginsWith" | "endsWith"
        | "containsBlanks" | "notContainsBlanks" | "containsErrors" | "notContainsErrors"
        | "duplicateValues" | "uniqueValues" | "timePeriod" | "top10" | "aboveAverage";

## Activity

    $ /bin/zsh -lc "sed -n '221,444p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/artifact_tool_docs/API_QUICK_START.md && sed -n '1,120p' /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/workflows/edit_workflows.md"
    status: Completed · exit 0
      # Editing an existing spreadsheet
      
      Treat existing workbook as the reference: preserve its structure, formula patterns, formatting, terminology, and navigation and extend nearby conventions unless the user explicitly requests a change.
      
      User requests always take priority over any rules in this file.
      
      ## Safety rules
      - Do not add, remove, rename, reorder, or split tabs unless requested or required.
      - Before modifying: ALWAYS study and match the existing format, style and conventions when making edits by rendering and viewing the image. Read related values and formulas.
      
      ## Important guidelines
      - Prioritize consistency unless it conflicts with user request: Ensure existing formulas, layouts, structures, and patterns are consistent. For example, if asked to add another column or row to a table and there is conditional formatting applied to the whole table, it should extend to the new column or rows as well.
      - Keep edits targeted unless a broader change is clearly necessary. Exceptions are when there's dependencies, e.g. a dynamic chart that is based on the range of values in a table and a new row is added, the chart should also update.
      - Change only requested cells and directly affected formulas/charts. Preserve unrelated tabs, formulas, formatting, validations, named ranges, comments, protection, hidden/grouped rows/columns, freeze panes and chart content. Do not add sheets, rows, columns or helpers unless requested.
      - Never overwrite formatting for spreadsheets with established formats, unless requested or to extend an added range.
      - Preserve native tables, structured references, pivot sources, shared formulas, filters, external links, INDIRECT routing and calculation/iteration settings. Do not flatten formulas or rebuild unrelated features for convenience.
      - For visual fixes, start with the smallest plausible local change. Do not apply sheet-wide autofit, wrapping, or restyling unless requested.
      
      ## Formula Rules
      
      For formula edits, follow the user's request first; otherwise preserve valid existing conventions before applying defaults for new formulas.
      
      - Preserve valid existing formula conventions, structure and references to editable inputs unless the user requests otherwise. Look at a couple examples in the requested edit area before making changes.
      - If there are any errors with the original workbook, unrelated to the task at hand, do not fix them arbitrarily. Instead, summarize the issues to the user and ask if they want them fixed.

## Activity

    $ /bin/zsh -lc "git status --short --branch && git log --oneline -6 && rg -n \"AIR_PREHEAT_END_S|selected = selected|load_air_data|np.interp\" solution/task2/script/solve_task2.py && /Users/jiaqiaosu/miniconda3/bin/python -c \"import importlib.util,pandas as pd,numpy as np; p='solution/task2/script/solve_task2.py'; spec=importlib.util.spec_from_file_location('task2',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); raw=pd.read_excel('problem/附件/附件1.xlsx'); print('附件时间范围',raw['时间'].min(),raw['时间'].max(),'行数',len(raw)); t,T,C=m.load_air_data(); print('当前load_air_data范围',t[0],t[-1],'行数',len(t)); print('当前10800边界',np.interp(10800,t,T),np.interp(10800,t,C)); print('真实10800边界',np.interp(10800,raw['时间'],raw['温度']),np.interp(10800,raw['时间'],raw['水分浓度'])); assert t[-1] < 10800 and not np.isclose(np.interp(10800,t,T),np.interp(10800,raw['时间'],raw['温度'])); print('RED: 已复现1800秒截断错误')\" && find /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime -name mark_artifact_operation_started.mjs -print"
    status: Completed · exit 0
      附件时间范围 0 14400 行数 241
      当前load_air_data范围 0.0 1800.0 行数 31
      当前10800边界 41.513 0.03307
      真实10800边界 50.195 0.04977
      RED: 已复现1800秒截断错误
      /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/container_tools/mark_artifact_operation_started.mjs
      /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/pdf/26.909.12148/skills/pdf/container_tools/mark_artifact_operation_started.mjs
      /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations/container_tools/mark_artifact_operation_started.mjs
      /Users/jiaqiaosu/.codex/plugins/cache/openai-primary-runtime/documents/26.909.12148/skills/documents/container_tools/mark_artifact_operation_started.mjs

## Assistant

根因已复现：附件实际覆盖 `0–14400 s`；当前 `load_air_data()` 仅保留 31 行到 1800 s，导致 10800 s 边界错误地保持为 `41.513 °C / 0.03307`，真实插值应为 `50.195 °C / 0.04977`。这是唯一需要修改的数据流点。Spreadsheet skill 要求的编辑标记会在重生成 XLSX 前执行；实际写入继续沿用现有模板脚本，以避免改变任何输出结构或样式。

## Activity

    $ /bin/zsh -lc 'node container_tools/mark_artifact_operation_started.mjs --operation-kind edit --expected-output-count 1 --output-format xlsx'
    status: Completed · exit 0

## Activity

    Started `/root/fix_task2_boundary`

## Activity

    agent tool: Wait · Completed

## Assistant

状态：worker 正在执行最小补丁和完整 3 h 重算。当前无阻塞；不会提交已暂存的 `context/context-task2-1_xby.md` 或任何 `.DS_Store`。下一验收点是新的表 3/表 4、时间步与空间敏感性结果。

## Activity

    agent tool: Wait · Completed

## Activity

    $ /bin/zsh -lc "git status --short --branch && git log --oneline -5 && git diff -- solution/task2/script/solve_task2.py | sed -n '1,180p'"
    status: Completed · exit 0
      ## main...origin/main
      A  context/context-task2-1_xby.md
       M solution/task2/answer/result2.xlsx
       M solution/task2/answer/task2_all_results.csv
       M solution/task2/script/solve_task2.py
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/
      94ffe31 修正问题二结果模板格式
      f423a75 统一问题一结果文件格式
      9375a01 生成问题二最终结果并完成数值验证
      e1db607 完成问题二三小时热质耦合求解
      a520f6d 完成问题二动态物性求解框架
      diff --git a/solution/task2/script/solve_task2.py b/solution/task2/script/solve_task2.py
      index 515d9be..effa9e6 100644
      --- a/solution/task2/script/solve_task2.py
      +++ b/solution/task2/script/solve_task2.py
      @@ -27,7 +27,6 @@ LENGTH_M = 0.25  # 一维径向守恒式中约去，保留作题目参数记录
       BASE_DR_M = 0.000125
       INITIAL_TEMPERATURE_C = 28.0
       INITIAL_MOISTURE_KGKG = 2.55
      -AIR_PREHEAT_END_S = 1800.0
       FINAL_TIME_S = 10800.0
       OUTPUT_DT_S = 1.0
       OUTPUT_RADIUS_CM = np.arange(0.0, 2.0000001, 0.1)
      @@ -60,13 +59,9 @@ DEFAULT_CSV_PATH = (
      
       def load_air_data(
           path: str | Path = DEFAULT_DATA_PATH,
      -    preheat_end_s: float = AIR_PREHEAT_END_S,
      +    required_end_s: float = FINAL_TIME_S,
       ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
      -    """读取附件1的预热段，并对 1800 s 后使用末端值保持。
      -
      -    附件中可能还包含 1800 s 以后的记录；问题二按题目给出的最小假设，
      -    只把 0--1800 s 作为预热边界，后续时间由 np.interp 的端点保持处理。
      -    """
      +    """读取附件1的全部烘房边界数据，供求解区间内分段线性插值。"""
      
           frame = pd.read_excel(Path(path))
           column_map = {str(column).strip(): column for column in frame.columns}
      @@ -80,17 +75,16 @@ def load_air_data(
           for column in required:
               selected[column] = pd.to_numeric(selected[column], errors="raise")
           selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")
      -    selected = selected[selected["时间"] <= preheat_end_s + 1.0e-10]
      
           time_s = selected["时间"].to_numpy(dtype=float)
           air_temperature_C = selected["温度"].to_numpy(dtype=float)
           air_moisture_kgkg = selected["水分浓度"].to_numpy(dtype=float)
           if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
      -        raise ValueError("附件1预热段时间必须包含至少两个严格递增时间点")
      -    if time_s[0] > 1.0e-10 or time_s[-1] < preheat_end_s - 1.0e-10:
      -        raise ValueError("附件1预热段未覆盖 0--1800 s")
      +        raise ValueError("附件1时间必须包含至少两个严格递增时间点")
      +    if time_s[0] > 1.0e-10 or time_s[-1] < required_end_s - 1.0e-10:
      +        raise ValueError(f"附件1烘房边界数据未覆盖 0--{required_end_s:g} s")
           if not np.all(np.isfinite(np.column_stack((time_s, air_temperature_C, air_moisture_kgkg)))):
      -        raise ValueError("附件1预热段包含非有限数值")
      +        raise ValueError("附件1烘房边界数据包含非有限数值")
           return time_s, air_temperature_C, air_moisture_kgkg
      
      
      @@ -317,7 +311,9 @@ def solve_task2(
           if not np.isclose(ratio, output_stride, atol=1.0e-10):
               raise ValueError("为避免额外插值，output_dt_s 必须是 time_step_s 的整数倍")
      
      -    air_time_s, air_temperature, air_moisture = load_air_data(data_path)
      +    air_time_s, air_temperature, air_moisture = load_air_data(
      +        data_path, required_end_s=t_end_s
      +    )
           radii_m, faces_m, radial_measure_m2 = control_volume_geometry(RADIUS_M, dr_m)
           output_indices = _output_indices(radii_m)
           n_nodes = radii_m.size

## Activity

    agent tool: Wait · Completed

## Assistant

状态：最小代码差异已经形成，只删除 1800 s 截断，并增加“附件必须覆盖本次求解终点”的校验；其余求解逻辑无改动。新 XLSX/CSV 已生成，worker 正在完成逐点一致性、`dt=0.5 s` 和 `dr` 减半复核后提交。

## Activity

    Completed `/root/fix_task2_boundary`

## Activity

    agent tool: Wait · Completed

## Assistant

worker 已完成重算并提交 `ed97452…`。修复后 10800 s 的真实边界为 `50.195 °C / 0.04977 kg/kg`，最终药材温度和水分结果已明显更新。现在进行 root 验收：核对 commit 只有目标三文件、脚本只改边界读取，并独立比对附件插值、CSV、XLSX 和关键表。

## Activity

    Started `/root/review_boundary_fix`

## Activity

    $ /bin/zsh -lc "git status --short --branch && git show --stat --oneline ed97452fa44a941d72bf2dccdfa3ab989f24a132 && git show --name-only --format='' ed97452fa44a941d72bf2dccdfa3ab989f24a132 && git diff 94ffe31..ed97452 -- solution/task2/script/solve_task2.py && git diff --check 94ffe31..ed97452 && git diff --exit-code -- problem/附件/附件1.xlsx problem/附件/附件3/result2.xlsx"
    status: Completed · exit 0
      solution/task2/answer/result2.xlsx
      solution/task2/answer/task2_all_results.csv
      solution/task2/script/solve_task2.py
      diff --git a/solution/task2/script/solve_task2.py b/solution/task2/script/solve_task2.py
      index 515d9be..effa9e6 100644
      --- a/solution/task2/script/solve_task2.py
      +++ b/solution/task2/script/solve_task2.py
      @@ -27,7 +27,6 @@ LENGTH_M = 0.25  # 一维径向守恒式中约去，保留作题目参数记录
       BASE_DR_M = 0.000125
       INITIAL_TEMPERATURE_C = 28.0
       INITIAL_MOISTURE_KGKG = 2.55
      -AIR_PREHEAT_END_S = 1800.0
       FINAL_TIME_S = 10800.0
       OUTPUT_DT_S = 1.0
       OUTPUT_RADIUS_CM = np.arange(0.0, 2.0000001, 0.1)
      @@ -60,13 +59,9 @@ DEFAULT_CSV_PATH = (
      
       def load_air_data(
           path: str | Path = DEFAULT_DATA_PATH,
      -    preheat_end_s: float = AIR_PREHEAT_END_S,
      +    required_end_s: float = FINAL_TIME_S,
       ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
      -    """读取附件1的预热段，并对 1800 s 后使用末端值保持。
      -
      -    附件中可能还包含 1800 s 以后的记录；问题二按题目给出的最小假设，
      -    只把 0--1800 s 作为预热边界，后续时间由 np.interp 的端点保持处理。
      -    """
      +    """读取附件1的全部烘房边界数据，供求解区间内分段线性插值。"""
      
           frame = pd.read_excel(Path(path))
           column_map = {str(column).strip(): column for column in frame.columns}
      @@ -80,17 +75,16 @@ def load_air_data(
           for column in required:
               selected[column] = pd.to_numeric(selected[column], errors="raise")
           selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")
      -    selected = selected[selected["时间"] <= preheat_end_s + 1.0e-10]
      
           time_s = selected["时间"].to_numpy(dtype=float)
           air_temperature_C = selected["温度"].to_numpy(dtype=float)
           air_moisture_kgkg = selected["水分浓度"].to_numpy(dtype=float)
           if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
      -        raise ValueError("附件1预热段时间必须包含至少两个严格递增时间点")
      -    if time_s[0] > 1.0e-10 or time_s[-1] < preheat_end_s - 1.0e-10:
      -        raise ValueError("附件1预热段未覆盖 0--1800 s")
      +        raise ValueError("附件1时间必须包含至少两个严格递增时间点")
      +    if time_s[0] > 1.0e-10 or time_s[-1] < required_end_s - 1.0e-10:
      +        raise ValueError(f"附件1烘房边界数据未覆盖 0--{required_end_s:g} s")
           if not np.all(np.isfinite(np.column_stack((time_s, air_temperature_C, air_moisture_kgkg)))):
      -        raise ValueError("附件1预热段包含非有限数值")
      +        raise ValueError("附件1烘房边界数据包含非有限数值")
           return time_s, air_temperature_C, air_moisture_kgkg
      
      
      @@ -317,7 +311,9 @@ def solve_task2(
           if not np.isclose(ratio, output_stride, atol=1.0e-10):
               raise ValueError("为避免额外插值，output_dt_s 必须是 time_step_s 的整数倍")
      
      -    air_time_s, air_temperature, air_moisture = load_air_data(data_path)
      +    air_time_s, air_temperature, air_moisture = load_air_data(
      +        data_path, required_end_s=t_end_s
      +    )
           radii_m, faces_m, radial_measure_m2 = control_volume_geometry(RADIUS_M, dr_m)
           output_indices = _output_indices(radii_m)
           n_nodes = radii_m.size

## Activity

    $ /bin/zsh -lc "/Users/jiaqiaosu/miniconda3/bin/python -c \"import importlib.util,pandas as pd,numpy as np; from openpyxl import load_workbook; spec=importlib.util.spec_from_file_location('m','solution/task2/script/solve_task2.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); raw=pd.read_excel('problem/附件/附件1.xlsx'); t,Ta,Ca=m.load_air_data(); assert t[0]==0 and t[-1]==14400 and len(t)==241; assert np.isclose(np.interp(10800,t,Ta),50.195) and np.isclose(np.interp(10800,t,Ca),0.04977); df=pd.read_csv('solution/task2/answer/task2_all_results.csv'); assert list(df.columns)==['time_s','time_h','radius_cm','temperature_C','moisture_kgkg']; assert len(df)==226821 and df.time_s.nunique()==10801 and df.radius_cm.nunique()==21; assert df[['time_s','radius_cm']].drop_duplicates().shape[0]==226821; assert np.array_equal(df.time_s.unique(),np.arange(10801)); assert np.allclose(df.radius_cm.unique(),np.arange(21)/10); assert np.isfinite(df[['temperature_C','moisture_kgkg']]).all().all() and df.moisture_kgkg.min()>=0; T=df.temperature_C.to_numpy().reshape(10801,21); C=df.moisture_kgkg.to_numpy().reshape(10801,21); assert np.min(np.diff(T,axis=0))>=0 and np.max(np.diff(C,axis=0))<=0; assert np.all(np.diff(T[-1])>=0) and np.all(np.diff(C[-1])<=0); wb=load_workbook('solution/task2/answer/result2.xlsx',read_only=True,data_only=True); assert wb.sheetnames==['温度','水分浓度']; arr=[]
for sn in wb.sheetnames:
 ws=wb[sn]; assert ws.max_row==10802 and ws.max_column==22; rows=ws.iter_rows(values_only=True); h=next(rows); assert h[0]=='时间\\\\到药材中心的距离' and np.allclose(h[1:],np.arange(21)/10); data=list(rows); assert np.array_equal(np.array([x[0] for x in data]),np.arange(10801)); arr.append(np.array([x[1:] for x in data],float))
assert np.array_equal(arr[0],T) and np.array_equal(arr[1],C); key=df[df.time_s.isin([1800,3600,5400,7200,9000,10800]) & df.radius_cm.isin([0,.5,1,1.5,2])]; assert len(key)==30; print('root验收: PASS'); print(f'air={t[0]:.0f}..{t[-1]:.0f}s rows={len(t)} boundary10800={np.interp(10800,t,Ta):.3f},{np.interp(10800,t,Ca):.5f}'); print(f'csv_rows={len(df)} xlsx_csv_maxdiff={np.max(np.abs(arr[0]-T)):.1f},{np.max(np.abs(arr[1]-C)):.1f}'); print(f'T_range={T.min():.4f}..{T.max():.4f} C_range={C.min():.4f}..{C.max():.4f} maxstep={np.max(np.diff(T,axis=0)):.4f},{np.max(np.abs(np.diff(C,axis=0))):.4f}'); print(key.to_csv(index=False))\""
    status: Failed · exit 1
      Traceback (most recent call last):
        File "<string>", line 1, in <module>
          import importlib.util,pandas as pd,numpy as np; from openpyxl import load_workbook; spec=importlib.util.spec_from_file_location('m','solution/task2/script/solve_task2.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); raw=pd.read_excel('problem/附件/附件1.xlsx'); t,Ta,Ca=m.load_air_data(); assert t[0]==0 and t[-1]==14400 and len(t)==241; assert np.isclose(np.interp(10800,t,Ta),50.195) and np.isclose(np.interp(10800,t,Ca),0.04977); df=pd.read_csv('solution/task2/answer/task2_all_results.csv'); assert list(df.columns)==['time_s','time_h','radius_cm','temperature_C','moisture_kgkg']; assert len(df)==226821 and df.time_s.nunique()==10801 and df.radius_cm.nunique()==21; assert df[['time_s','radius_cm']].drop_duplicates().shape[0]==226821; assert np.array_equal(df.time_s.unique(),np.arange(10801)); assert np.allclose(df.radius_cm.unique(),np.arange(21)/10); assert np.isfinite(df[['temperature_C','moisture_kgkg']]).all().all() and df.moisture_kgkg.min()>=0; T=df.temperature_C.to_numpy().reshape(10801,21); C=df.moisture_kgkg.to_numpy().reshape(10801,21); assert np.min(np.diff(T,axis=0))>=0 and np.max(np.diff(C,axis=0))<=0; assert np.all(np.diff(T[-1])>=0) and np.all(np.diff(C[-1])<=0); wb=load_workbook('solution/task2/answer/result2.xlsx',read_only=True,data_only=True); assert wb.sheetnames==['温度','水分浓度']; arr=[]
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      AssertionError

## Assistant

root 文件结构和边界断言已通过；额外加入的“所有节点每秒严格单调”断言失败。附件1是真实时变数据，局部小幅波动并不等于数值爆炸，因此我不会据此改模型。正在定位最大反向变化，并按题目要求判断连续性与物理范围。

## Activity

    $ /bin/zsh -lc "/Users/jiaqiaosu/miniconda3/bin/python -c \"import pandas as pd,numpy as np; df=pd.read_csv('solution/task2/answer/task2_all_results.csv'); T=df.temperature_C.to_numpy().reshape(10801,21); C=df.moisture_kgkg.to_numpy().reshape(10801,21); dT=np.diff(T,axis=0); dC=np.diff(C,axis=0); print('min_dT',dT.min(),np.unravel_index(np.argmin(dT),dT.shape)); print('max_dT',dT.max(),np.unravel_index(np.argmax(dT),dT.shape)); print('max_dC',dC.max(),np.unravel_index(np.argmax(dC),dC.shape)); print('min_dC',dC.min(),np.unravel_index(np.argmin(dC),dC.shape)); print('final radial T min',np.diff(T[-1]).min(),'C max',np.diff(C[-1]).max())\""
    status: Completed · exit 0
      min_dT -0.0009999999999976694 (np.int64(10439), np.int64(20))
      max_dT 0.00560000000000116 (np.int64(1316), np.int64(20))
      max_dC 0.0 (np.int64(0), np.int64(0))
      min_dC -0.02059999999999995 (np.int64(0), np.int64(20))
      final radial T min 0.0002999999999957481 C max -0.0020000000000000018

## User

根据 handoff/task2_handoff.md 优化一下当前的任务二

## Assistant

状态：先以 `handoff/task2_handoff.md` 为唯一优化依据，核对当前 `solve_task2.py` 和最新提交，明确“要优化什么、哪些必须保持不变”；在确认范围后再交给 `luna-worker` 执行。这里会使用轻量的 `brainstorming` 做需求边界判断，避免把“优化”扩展成无关重构。

## Activity

    $ /bin/zsh -lc "git status --short --branch && git log --oneline -8 && wc -l handoff/task2_handoff.md && sed -n '1,360p' /Users/jiaqiaosu/.agents/skills/brainstorming/SKILL.md && sed -n '1,520p' handoff/task2_handoff.md"
    status: Completed · exit 0
      ## main...origin/main [ahead 3]
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/
      8af6846 更新问题三CN长期计算结果
      0f56894 完善问题三敏感性比较验证
      c0e35aa 重构问题三CN调和平均求解器
      959722d 优化了交接文档格式
      80c17df 补充任务三和任务四的上下文，以及部分任务四交接文档
      ef39808 修正问题四交接文档方程与迭代说明
      3b2119b 补充问题四移动边界模型交接文档
      2b0d204 生成问题四最终数值结果
          1668 handoff/task2_handoff.md
      ---
      name: brainstorming
      description: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."
      ---
      
      # Brainstorming Ideas Into Designs
      
      Help turn ideas into fully formed designs and specs through natural collaborative dialogue.
      
      Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design and get user approval.
      
      <HARD-GATE>
      Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
      </HARD-GATE>
      
      ## Anti-Pattern: "This Is Too Simple To Need A Design"
      
      Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.
      
      ## Checklist
      
      You MUST create a task for each of these items and complete them in order:
      
      1. **Explore project context** — check files, docs, recent commits
      2. **Offer visual companion** (if topic will involve visual questions) — this is its own message, not combined with a clarifying question. See the Visual Companion section below.
      3. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
      4. **Propose 2-3 approaches** — with trade-offs and your recommendation
      5. **Present design** — in sections scaled to their complexity, get user approval after each section
      6. **Write design doc** — save to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` and commit
      7. **Spec self-review** — quick inline check for placeholders, contradictions, ambiguity, scope (see below)
      8. **User reviews written spec** — ask user to review the spec file before proceeding
      9. **Transition to implementation** — invoke writing-plans skill to create implementation plan
      
      ## Process Flow
      
      ```dot
      digraph brainstorming {
          "Explore project context" [shape=box];
          "Visual questions ahead?" [shape=diamond];
          "Offer Visual Companion\n(own message, no other content)" [shape=box];
          "Ask clarifying questions" [shape=box];
          "Propose 2-3 approaches" [shape=box];
          "Present design sections" [shape=box];
          "User approves design?" [shape=diamond];
          "Write design doc" [shape=box];
          "Spec self-review\n(fix inline)" [shape=box];
          "User reviews spec?" [shape=diamond];
          "Invoke writing-plans skill" [shape=doublecircle];
      
          "Explore project context" -> "Visual questions ahead?";
          "Visual questions ahead?" -> "Offer Visual Companion\n(own message, no other content)" [label="yes"];
          "Visual questions ahead?" -> "Ask clarifying questions" [label="no"];
          "Offer Visual Companion\n(own message, no other content)" -> "Ask clarifying questions";
          "Ask clarifying questions" -> "Propose 2-3 approaches";
          "Propose 2-3 approaches" -> "Present design sections";
          "Present design sections" -> "User approves design?";
          "User approves design?" -> "Present design sections" [label="no, revise"];
          "User approves design?" -> "Write design doc" [label="yes"];
          "Write design doc" -> "Spec self-review\n(fix inline)";
          "Spec self-review\n(fix inline)" -> "User reviews spec?";
          "User reviews spec?" -> "Write design doc" [label="changes requested"];
          "User reviews spec?" -> "Invoke writing-plans skill" [label="approved"];
      }
      ```
      
      **The terminal state is invoking writing-plans.** Do NOT invoke frontend-design, mcp-builder, or any other implementation skill. The ONLY skill you invoke after brainstorming is writing-plans.
      
      ## The Process
      
      **Understanding the idea:**
      
      - Check out the current project state first (files, docs, recent commits)
      - Before asking detailed questions, assess scope: if the request describes multiple independent subsystems (e.g., "build a platform with chat, file storage, billing, and analytics"), flag this immediately. Don't spend questions refining details of a project that needs to be decomposed first.
      - If the project is too large for a single spec, help the user decompose into sub-projects: what are the independent pieces, how do they relate, what order should they be built? Then brainstorm the first sub-project through the normal design flow. Each sub-project gets its own spec → plan → implementation cycle.
      - For appropriately-scoped projects, ask questions one at a time to refine the idea
      - Prefer multiple choice questions when possible, but open-ended is fine too
      - Only one question per message - if a topic needs more exploration, break it into multiple questions
      - Focus on understanding: purpose, constraints, success criteria
      
      **Exploring approaches:**
      
      - Propose 2-3 different approaches with trade-offs
      - Present options conversationally with your recommendation and reasoning
      - Lead with your recommended option and explain why
      
      **Presenting the design:**
      
      - Once you believe you understand what you're building, present the design
      - Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced
      - Ask after each section whether it looks right so far
      - Cover: architecture, components, data flow, error handling, testing
      - Be ready to go back and clarify if something doesn't make sense
      
      **Design for isolation and clarity:**
      
      - Break the system into smaller units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently
      - For each unit, you should be able to answer: what does it do, how do you use it, and what does it depend on?
      - Can someone understand what a unit does without reading its internals? Can you change the internals without breaking consumers? If not, the boundaries need work.
      - Smaller, well-bounded units are also easier for you to work with - you reason better about code you can hold in context at once, and your edits are more reliable when files are focused. When a file grows large, that's often a signal that it's doing too much.
      
      **Working in existing codebases:**
      
      - Explore the current structure before proposing changes. Follow existing patterns.
      - Where existing code has problems that affect the work (e.g., a file that's grown too large, unclear boundaries, tangled responsibilities), include targeted improvements as part of the design - the way a good developer improves code they're working in.
      - Don't propose unrelated refactoring. Stay focused on what serves the current goal.
      
      ## After the Design
      
      **Documentation:**
      
      - Write the validated design (spec) to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
        - (User preferences for spec location override this default)
      - Use elements-of-style:writing-clearly-and-concisely skill if available
      - Commit the design document to git
      
      **Spec Self-Review:**
      After writing the spec document, look at it with fresh eyes:
      
      1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections, or vague requirements? Fix them.
      2. **Internal consistency:** Do any sections contradict each other? Does the architecture match the feature descriptions?
      3. **Scope check:** Is this focused enough for a single implementation plan, or does it need decomposition?
      4. **Ambiguity check:** Could any requirement be interpreted two different ways? If so, pick one and make it explicit.
      
      Fix any issues inline. No need to re-review — just fix and move on.
      
      **User Review Gate:**
      After the spec review loop passes, ask the user to review the written spec before proceeding:
      
      > "Spec written and committed to `<path>`. Please review it and let me know if you want to make any changes before we start writing out the implementation plan."
      
      Wait for the user's response. If they request changes, make them and re-run the spec review loop. Only proceed once the user approves.
      
      **Implementation:**
      
      - Invoke the writing-plans skill to create a detailed implementation plan
      - Do NOT invoke any other skill. writing-plans is the next step.
      
      ## Key Principles
      
      - **One question at a time** - Don't overwhelm with multiple questions
      - **Multiple choice preferred** - Easier to answer than open-ended when possible
      - **YAGNI ruthlessly** - Remove unnecessary features from all designs
      - **Explore alternatives** - Always propose 2-3 approaches before settling
      - **Incremental validation** - Present design, get approval before moving on
      - **Be flexible** - Go back and clarify when something doesn't make sense
      
      ## Visual Companion
      
      A browser-based companion for showing mockups, diagrams, and visual options during brainstorming. Available as a tool — not a mode. Accepting the companion means it's available for questions that benefit from visual treatment; it does NOT mean every question goes through the browser.
      
      **Offering the companion:** When you anticipate that upcoming questions will involve visual content (mockups, layouts, diagrams), offer it once for consent:
      > "Some of what we're working on might be easier to explain if I can show it to you in a web browser. I can put together mockups, diagrams, comparisons, and other visuals as we go. This feature is still new and can be token-intensive. Want to try it? (Requires opening a local URL)"
      
      **This offer MUST be its own message.** Do not combine it with clarifying questions, context summaries, or any other content. The message should contain ONLY the offer above and nothing else. Wait for the user's response before continuing. If they decline, proceed with text-only brainstorming.
      
      **Per-question decision:** Even after the user accepts, decide FOR EACH QUESTION whether to use the browser or the terminal. The test: **would the user understand this better by seeing it than reading it?**
      
      - **Use the browser** for content that IS visual — mockups, wireframes, layout comparisons, architecture diagrams, side-by-side visual designs
      - **Use the terminal** for content that is text — requirements questions, conceptual choices, tradeoff lists, A/B/C/D text options, scope decisions
      
      A question about a UI topic is not automatically a visual question. "What does personality mean in this context?" is a conceptual question — use the terminal. "Which wizard layout works better?" is a visual question — use the browser.
      
      If they agree to the companion, read the detailed guide before proceeding:
      `skills/brainstorming/visual-companion.md`
      # A题问题二：融合型温度—水分双向耦合全流程数学模型
      
      ## 1. 问题定义
      
      药材近似为长
      
      $$
      L=25\ \mathrm{cm}
      $$
      
      、半径
      
      $$
      R=2\ \mathrm{cm}
      $$
      
      的圆柱体。烘干初始时刻为
      
      $$
      T(r,0)=28^\circ\mathrm C,
      \qquad
      C(r,0)=2.55\ \mathrm{kg/kg}.
      $$
      
      问题二要求建立整个烘干过程中药材内部温度场
      
      $$
      T(r,t)
      $$
      
      和干基含水率场
      
      $$
      C(r,t)
      $$
      
      的变化模型，并统一使用附录 3 给出的状态相关经验公式。
      
      计算区间为
      
      $$
      0\le t\le10800\ \mathrm s,
      \qquad
      0\le r\le0.02\ \mathrm m.
      $$
      
      附件 1 中烘房环境数据覆盖 $0\sim14400\ \mathrm s$，因此问题二前三小时的计算区间全部位于附件数据范围内。
      
      ---
      
      ## 2. 模型结构
      
      该模型由以下部分组成：
      
      | 模型环节 | 采用形式 |
      |---|---|
      | 几何模型 | 固定半径圆柱一维径向模型 |
      | 温度控制方程 | 变物性非稳态 Fourier 导热方程 |
      | 水分控制方程 | 变扩散系数 Fick 扩散方程 |
      | 中心边界 | 轴对称零通量条件 |
      | 表面热边界 | Newton 对流换热 Robin 边界 |
      | 表面水分边界 | 对流传质 Robin 边界 |
      | 外部环境数据 | 附件 1 分段线性插值 |
      | 空间离散 | 圆柱径向有限体积法 |
      | 界面物性 | 调和平均 |
      | 时间离散 | 后向欧拉 |
      | 非线性耦合 | 同状态块 Picard 迭代 |
      | 线性系统 | 三对角线性方程组直接求解 |
      
      ---
      
      ## 3. 模型假设
      
      1. 药材视为均匀、各向同性的规则圆柱体。
      
      2. 仅考虑径向温度和水分变化，忽略轴向梯度。
      
      3. 问题二中药材半径保持
      
      $$
      R=0.02\ \mathrm m
      $$
      
      不变，不考虑尺寸收缩。
      
      4. 初始温度和初始干基含水率在整个径向上均匀分布。
      
      5. 药材内部复杂孔隙结构和不同形态水分的迁移统一用题目给出的有效扩散系数 $D(T,C)$ 表示。
      
      6. 密度、比热容、导热系数和水分扩散系数由局部当前状态决定。
      
      7. 烘房环境在药材圆柱侧表面上均匀分布。
      
      8. 表面对流换热系数和对流传质系数采用
      
      $$
      h=25\ \mathrm{W/(m^2\,K)},
      $$
      
      $$
      h_m=8\times10^{-7}\ \mathrm{m/s}.
      $$
      
      9. 附件 1 中的烘房水分浓度直接作为表面对流传质边界中的外部有效水分浓度
      
      $$
      C_\infty(t).
      $$
      
      10. 模型不包含蒸发潜热、辐射换热、内部热源、化学反应和相变动力学。
      
      11. 温度方程的局部储热项采用
      
      $$
      \rho(C)c_p(C)\frac{\partial T}{\partial t},
      $$
      
      不展开为包含物性时间导数的其他形式。
      
      ---
      
      ## 4. 变量与参数
      
      | 符号 | 含义 | 单位 |
      |---|---|---|
      | $r$ | 距圆柱中心轴的径向距离 | m |
      | $R$ | 药材半径 | m |
      | $L$ | 药材长度 | m |
      | $t$ | 时间 | s |
      | $T(r,t)$ | 药材内部温度 | °C |
      | $T_K(r,t)$ | 药材绝对温度 | K |
      | $C(r,t)$ | 药材干基含水率 | kg/kg |
      | $T_\infty(t)$ | 烘房温度 | °C |
      | $C_\infty(t)$ | 烘房水分浓度 | kg/kg |
      | $\rho(C)$ | 密度 | kg/m³ |
      | $c_p(C)$ | 比热容 | J/(kg·K) |
      | $k(C)$ | 导热系数 | W/(m·K) |
      | $D(T,C)$ | 有效水分扩散系数 | m²/s |
      | $h$ | 对流换热系数 | W/(m²·K) |
      | $h_m$ | 对流传质系数 | m/s |
      
      ---
      
      ## 5. 烘房环境边界数据
      
      附件 1 给出离散时刻的烘房温度和水分浓度。
      
      对任一环境变量 $y(t)$，在相邻数据点
      
      $$
      (t_j,y_j),
      \qquad
      (t_{j+1},y_{j+1})
      $$
      
      之间采用分段线性插值：
      
      $$
      y(t)
      =
      y_j+
      \frac{y_{j+1}-y_j}{t_{j+1}-t_j}
      (t-t_j),
      \qquad
      t_j\le t\le t_{j+1}.
      $$
      
      由此分别得到
      
      $$
      T_\infty(t),
      \qquad
      C_\infty(t).
      $$
      
      在从 $t^n$ 推进至 $t^{n+1}$ 时，边界项使用
      
      $$
      T_\infty(t^{n+1}),
      \qquad
      C_\infty(t^{n+1}).
      $$
      
      ---
      
      ## 6. 附录 3 状态相关物性
      
      密度为
      
      $$
      \rho(C)=650+128C.
      $$
      
      比热容为
      
      $$
      c_p(C)
      =
      1450+2736\frac{C}{C+1}.
      $$
      
      导热系数为
      
      $$
      k(C)
      =
      0.21+0.38\frac{C}{C+1}.
      $$
      
      水分扩散系数为
      
      $$
      D(T,C)
      =
      2.4\times10^{-3}
      \exp\left(-\frac{0.45}{C}\right)
      \exp\left(-\frac{3850}{T_K}\right).
      $$
      
      其中
      
      $$
      T_K=T+273.15.
      $$
      
      因此 $D$ 的计算使用绝对温度 Kelvin，温度场本身可以用摄氏度保存和输出。
      
      由这些经验式形成以下状态依赖关系：
      
      $$
      C
      \rightarrow
      \rho(C),c_p(C),k(C)
      \rightarrow
      T,
      $$
      
      以及
      
      $$
      T,C
      \rightarrow
      D(T,C)
      \rightarrow
      C.
      $$
      
      整体关系可写为
      
      $$
      C
      \rightarrow
      (\rho,c_p,k)
      \rightarrow
      T
      \rightarrow
      D
      \rightarrow
      C.
      $$
      
      ---
      
      ## 7. 温度控制方程
      
      在轴对称圆柱坐标系中，温度满足
      
      $$
      \rho(C)c_p(C)
      \frac{\partial T}{\partial t}
      =
      \frac{1}{r}
      \frac{\partial}{\partial r}
      \left[
      rk(C)
      \frac{\partial T}{\partial r}
      \right],
      \qquad
      0<r<R.
      $$
      
      左端表示局部储热项，右端表示径向导热通量的散度。
      
      由于
      
      $$
      \rho=\rho(C),
      \qquad
      c_p=c_p(C),
      \qquad
      k=k(C),
      $$
      
      温度方程属于状态相关变系数非线性扩散方程。
      
      ---
      
      ## 8. 水分控制方程
      
      干基含水率满足
      
      $$
      \frac{\partial C}{\partial t}
      =
      \frac{1}{r}
      \frac{\partial}{\partial r}
      \left[
      rD(T,C)
      \frac{\partial C}{\partial r}
      \right],
      \qquad
      0<r<R.
      $$
      
      左端表示局部水分含量随时间的变化，右端表示径向扩散通量的散度。
      
      由于
      
      $$
      D=D(T,C),
      $$
      
      水分方程同时依赖温度场和含水率场。
      
      ---
      
      ## 9. 初始条件
      
      初始温度为
      
      $$
      T(r,0)=28^\circ\mathrm C,
      \qquad
      0\le r\le R.
      $$
      
      初始含水率为
      
      $$
      C(r,0)=2.55\ \mathrm{kg/kg},
      \qquad
      0\le r\le R.
      $$
      
      ---
      
      ## 10. 中心轴边界条件
      
      由于圆柱中心具有轴对称性，
      
      $$
      \left.
      \frac{\partial T}{\partial r}
      \right|_{r=0}
      =0,
      $$
      
      $$
      \left.
      \frac{\partial C}{\partial r}
      \right|_{r=0}
      =0.
      $$
      
      对应中心处热通量和水分通量均为零。
      
      ---
      
      ## 11. 表面对流边界条件
      
      ### 11.1 温度边界
      
      在药材表面 $r=R$：
      
      $$
      -k(C_s)
      \left.
      \frac{\partial T}{\partial r}
      \right|_{r=R}
      =
      h
      \left[
      T_s-T_\infty(t)
      \right],
      $$
      
      其中
      
      $$
      T_s=T(R,t),
      \qquad
      C_s=C(R,t).
      $$
      
      等价写为
      
      $$
      k(C_s)
      \left.
      \frac{\partial T}{\partial r}
      \right|_{r=R}
      =
      h
      \left[
      T_\infty(t)-T_s
      \right].
      $$
      
      ---
      
      ### 11.2 水分边界
      
      在药材表面：
      
      $$
      -D(T_s,C_s)
      \left.
      \frac{\partial C}{\partial r}
      \right|_{r=R}
      =
      h_m
      \left[
      C_s-C_\infty(t)
      \right].
      $$
      
      等价写为
      
      $$
      D(T_s,C_s)
      \left.
      \frac{\partial C}{\partial r}
      \right|_{r=R}
      =
      h_m
      \left[
      C_\infty(t)-C_s
      \right].
      $$
      
      ---
      
      # 12. 空间离散
      
      ## 12.1 径向有限体积网格
      
      取径向步长
      
      $$
      \Delta r
      =
      5\times10^{-5}\ \mathrm m
      =
      0.005\ \mathrm{cm}.
      $$
      
      径向节点定义为
      
      $$
      r_i=i\Delta r,
      \qquad
      i=0,1,\ldots,N.
      $$
      
      其中
      
      $$
      N=\frac{R}{\Delta r}=400.
      $$
      
      因此共有
      
      $$
      401
      $$
      
      个径向节点。
      
      节点包括
      
      $$
      r_0=0
      $$
      
      和
      
      $$
      r_N=R.
      $$
      
      ---
      
      ## 12.2 控制体几何量
      
      内部节点的左右控制体面为
      
      $$
      r_{i-\frac12}
      =
      r_i-\frac{\Delta r}{2},
      $$
      
      $$
      r_{i+\frac12}
      =
      r_i+\frac{\Delta r}{2}.
      $$
      
      除去圆柱积分中的公共因子 $2\pi L$，第 $i$ 个控制体的径向体积测度为
      
      $$
      V_i
      =
      \int_{r_{i-\frac12}}^{r_{i+\frac12}}r\,dr
      =
      \frac{
      r_{i+\frac12}^2-r_{i-\frac12}^2
      }{2}.
      $$

## Activity

    $ /bin/zsh -lc "sed -n '521,1040p' handoff/task2_handoff.md && sed -n '1041,1668p' handoff/task2_handoff.md"
    status: Completed · exit 0
      中心节点与表面节点均采用半控制体。
      
      中心位置：
      
      $$
      r_{-\frac12}=0.
      $$
      
      表面位置：
      
      $$
      r_{N+\frac12}=R.
      $$
      
      ---
      
      # 13. 界面物性
      
      相邻节点 $i$ 与 $i+1$ 之间的界面导热系数采用调和平均：
      
      $$
      k_{i+\frac12}
      =
      \frac{
      2k_i k_{i+1}
      }{
      k_i+k_{i+1}
      }.
      $$
      
      界面水分扩散系数为
      
      $$
      D_{i+\frac12}
      =
      \frac{
      2D_iD_{i+1}
      }{
      D_i+D_{i+1}
      }.
      $$
      
      相应的径向导热通量系数为
      
      $$
      G^T_{i+\frac12}
      =
      k_{i+\frac12}
      \frac{r_{i+\frac12}}{\Delta r},
      $$
      
      水分扩散通量系数为
      
      $$
      G^C_{i+\frac12}
      =
      D_{i+\frac12}
      \frac{r_{i+\frac12}}{\Delta r}.
      $$
      
      调和平均可由两个半网格区间的串联传递阻力得到。
      
      对于导热：
      
      $$
      R_T
      =
      \frac{\Delta r/2}{k_i}
      +
      \frac{\Delta r/2}{k_{i+1}}.
      $$
      
      定义等效界面导热系数满足
      
      $$
      R_T
      =
      \frac{\Delta r}{k_{i+\frac12}},
      $$
      
      可得
      
      $$
      k_{i+\frac12}
      =
      \frac{2k_ik_{i+1}}{k_i+k_{i+1}}.
      $$
      
      扩散系数 $D$ 的推导相同。
      
      ---
      
      # 14. 时间离散
      
      采用固定时间步
      
      $$
      \Delta t=0.5\ \mathrm s.
      $$
      
      时间节点为
      
      $$
      t^n=n\Delta t.
      $$
      
      时间导数采用后向欧拉：
      
      $$
      \frac{\partial T}{\partial t}
      \approx
      \frac{
      T_i^{n+1}-T_i^n
      }{
      \Delta t
      },
      $$
      
      $$
      \frac{\partial C}{\partial t}
      \approx
      \frac{
      C_i^{n+1}-C_i^n
      }{
      \Delta t
      }.
      $$
      
      新时刻的空间通量统一使用 $n+1$ 时刻的未知场，因此形成全隐式离散。
      
      ---
      
      # 15. 温度方程的有限体积离散
      
      在某一 Picard 迭代中，暂时固定
      
      $$
      \rho_i,\qquad
      c_{p,i},\qquad
      k_i.
      $$
      
      对于内部控制体 $i$：
      
      $$
      (\rho c_p)_iV_i
      \frac{
      T_i^{n+1}-T_i^n
      }{
      \Delta t
      }
      =
      G^T_{i+\frac12}
      \left(
      T_{i+1}^{n+1}-T_i^{n+1}
      \right)
      -
      G^T_{i-\frac12}
      \left(
      T_i^{n+1}-T_{i-1}^{n+1}
      \right).
      $$
      
      整理得到
      
      $$
      a_{P,i}^TT_i^{n+1}
      =
      a_{W,i}^TT_{i-1}^{n+1}
      +
      a_{E,i}^TT_{i+1}^{n+1}
      +
      b_i^T.
      $$
      
      其中
      
      $$
      a_{W,i}^T
      =
      \Delta tG^T_{i-\frac12},
      $$
      
      $$
      a_{E,i}^T
      =
      \Delta tG^T_{i+\frac12},
      $$
      
      $$
      a_{P,i}^T
      =
      (\rho c_p)_iV_i
      +
      a_{W,i}^T
      +
      a_{E,i}^T,
      $$
      
      $$
      b_i^T
      =
      (\rho c_p)_iV_iT_i^n.
      $$
      
      ---
      
      # 16. 水分方程的有限体积离散
      
      固定当前 Picard 迭代中的
      
      $$
      D_i=D(T_i,C_i).
      $$
      
      对于内部控制体：
      
      $$
      V_i
      \frac{
      C_i^{n+1}-C_i^n
      }{
      \Delta t
      }
      =
      G^C_{i+\frac12}
      \left(
      C_{i+1}^{n+1}-C_i^{n+1}
      \right)
      -
      G^C_{i-\frac12}
      \left(
      C_i^{n+1}-C_{i-1}^{n+1}
      \right).
      $$
      
      整理为
      
      $$
      a_{P,i}^CC_i^{n+1}
      =
      a_{W,i}^CC_{i-1}^{n+1}
      +
      a_{E,i}^CC_{i+1}^{n+1}
      +
      b_i^C.
      $$
      
      其中
      
      $$
      a_{W,i}^C
      =
      \Delta tG^C_{i-\frac12},
      $$
      
      $$
      a_{E,i}^C
      =
      \Delta tG^C_{i+\frac12},
      $$
      
      $$
      a_{P,i}^C
      =
      V_i
      +
      a_{W,i}^C
      +
      a_{E,i}^C,
      $$
      
      $$
      b_i^C
      =
      V_iC_i^n.
      $$
      
      ---
      
      # 17. 中心节点离散
      
      中心节点
      
      $$
      r_0=0
      $$
      
      处的内侧控制体面半径为零，因此
      
      $$
      G^T_{-\frac12}=0,
      \qquad
      G^C_{-\frac12}=0.
      $$
      
      由有限体积几何关系直接得到中心零通量条件，无需计算 $1/r$。
      
      ---
      
      # 18. 表面节点离散
      
      ## 18.1 温度表面节点
      
      最外侧控制体满足
      
      $$
      (\rho c_p)_NV_N
      \frac{
      T_N^{n+1}-T_N^n
      }{
      \Delta t
      }
      =
      G^T_{N-\frac12}
      \left(
      T_{N-1}^{n+1}-T_N^{n+1}
      \right)
      +
      Rh
      \left[
      T_\infty^{n+1}-T_N^{n+1}
      \right].
      $$
      
      对应矩阵系数增加
      
      $$
      a_{P,N}^T
      \leftarrow
      a_{P,N}^T
      +
      \Delta tRh,
      $$
      
      右端增加
      
      $$
      b_N^T
      \leftarrow
      b_N^T
      +
      \Delta tRhT_\infty^{n+1}.
      $$
      
      ---
      
      ## 18.2 水分表面节点
      
      最外侧水分控制体满足
      
      $$
      V_N
      \frac{
      C_N^{n+1}-C_N^n
      }{
      \Delta t
      }
      =
      G^C_{N-\frac12}
      \left(
      C_{N-1}^{n+1}-C_N^{n+1}
      \right)
      +
      Rh_m
      \left[
      C_\infty^{n+1}-C_N^{n+1}
      \right].
      $$
      
      对应
      
      $$
      a_{P,N}^C
      \leftarrow
      a_{P,N}^C
      +
      \Delta tRh_m,
      $$
      
      $$
      b_N^C
      \leftarrow
      b_N^C
      +
      \Delta tRh_mC_\infty^{n+1}.
      $$
      
      ---
      
      # 19. 非线性耦合求解
      
      由于
      
      $$
      \rho=\rho(C),
      $$
      
      $$
      c_p=c_p(C),
      $$
      
      $$
      k=k(C),
      $$
      
      $$
      D=D(T,C),
      $$
      
      每个新时间层的系数均依赖未知的 $T^{n+1},C^{n+1}$。
      
      因此在每个时间步内部进行 Picard 固定点迭代。
      
      ---
      
      ## 19.1 Picard 初值
      
      从已知时间层 $n$ 出发：
      
      $$
      T^{(0)}=T^n,
      $$
      
      $$
      C^{(0)}=C^n.
      $$
      
      ---
      
      ## 19.2 第 $m$ 次迭代
      
      根据同一组当前状态
      
      $$
      T^{(m)},C^{(m)}
      $$
      
      计算
      
      $$
      \rho^{(m)}
      =
      \rho(C^{(m)}),
      $$
      
      $$
      c_p^{(m)}
      =
      c_p(C^{(m)}),
      $$
      
      $$
      k^{(m)}
      =
      k(C^{(m)}),
      $$
      
      $$
      D^{(m)}
      =
      D(T^{(m)},C^{(m)}).
      $$
      
      再计算全部界面物性
      
      $$
      k_{i+\frac12}^{(m)},
      \qquad
      D_{i+\frac12}^{(m)}.
      $$
      
      在这一轮中冻结上述系数，分别建立并求解温度与水分三对角系统：
      
      $$
      T^{(m+1)}
      =
      \mathcal F_T
      \left(
      T^n;
      \rho^{(m)},
      c_p^{(m)},
      k^{(m)}
      \right),
      $$
      
      $$
      C^{(m+1)}
      =
      \mathcal F_C
      \left(
      C^n;
      D^{(m)}
      \right).
      $$
      
      两场均求解完成后，共同进入下一轮物性更新。
      
      该过程持续到 $T,C$ 同时满足收敛条件。
      
      ---
      
      ## 19.3 收敛判据
      
      温度最大模变化量定义为
      
      $$
      \varepsilon_T^{(m)}
      =
      \max_i
      \left|
      T_i^{(m+1)}-T_i^{(m)}
      \right|.
      $$
      
      水分最大模变化量定义为
      
      $$
      \varepsilon_C^{(m)}
      =
      \max_i
      \left|
      C_i^{(m+1)}-C_i^{(m)}
      \right|.
      $$
      
      计算中可设置
      
      $$
      \varepsilon_T
      \le10^{-8}\ ^\circ\mathrm C,
      $$
      
      $$
      \varepsilon_C
      \le10^{-10}\ \mathrm{kg/kg}.
      $$
      
      单个时间步最大 Picard 迭代次数设置为
      
      $$
      50.
      $$
      
      若达到最大迭代次数仍未满足收敛条件，则记录该时间步为非线性迭代失败，不继续将该步视为正常收敛结果。
      
      ---
      
      # 20. 三对角线性系统
      
      无论温度方程还是水分方程，有限体积离散后都只涉及
      
      $$
      i-1,\quad i,\quad i+1
      $$
      
      三个相邻节点。
      
      因此矩阵形式为
      
      $$
      A\mathbf x=\mathbf b,
      $$
      
      其中 $A$ 为三对角矩阵。
      
      温度方程：
      
      $$
      A_T\mathbf T^{(m+1)}
      =
      \mathbf b_T.
      $$
      
      水分方程：
      
      $$
      A_C\mathbf C^{(m+1)}
      =
      \mathbf b_C.
      $$
      
      可采用三对角直接算法或带状矩阵直接求解器求解。
      
      ---
      
      # 21. 完整计算流程
      
      ```mermaid
      flowchart TD
          A["读取附件1"] --> B["构造 T∞(t), C∞(t) 分段线性插值"]
          B --> C["建立径向有限体积网格"]
          C --> D["设置 T(r,0)=28°C<br/>C(r,0)=2.55 kg/kg"]
          D --> E["进入时间步 n → n+1"]
          E --> F["T^(0)=T^n<br/>C^(0)=C^n"]
          F --> G["由 T^(m), C^(m)<br/>计算 ρ, cp, k, D"]
          G --> H["调和平均得到界面 k、D"]
          H --> I["组装温度三对角系统"]
          H --> J["组装水分三对角系统"]
          I --> K["求 T^(m+1)"]
          J --> L["求 C^(m+1)"]
          K --> M["检查 T、C Picard 收敛"]
          L --> M
          M -- "未收敛" --> G
          M -- "收敛" --> N["接受 T^(n+1), C^(n+1)"]
          N --> O["按输出时间保存结果"]
          O --> P{"t < 10800 s"}
          P -- "是" --> E
          P -- "否" --> Q["形成完整温度场和水分场"]
      ```
      
      对应计算顺序为：
      
      1. 读取附件 1；
      2. 构造 $T_\infty(t),C_\infty(t)$；
      3. 建立径向有限体积网格；
      4. 设置初始温度和含水率；
      5. 进入下一时间步；
      6. 使用上一时间层状态初始化 Picard；
      7. 根据当前 $T,C$ 更新 $\rho,c_p,k,D$；
      8. 计算界面调和平均；
      9. 组装温度和水分线性系统；
      10. 分别求解新的温度场和水分场；
      11. 判断 Picard 收敛；
      12. 未收敛则更新当前状态继续迭代；
      13. 收敛后接受新的时间层；
      14. 保存题目要求的时间和径向节点数据；
      15. 重复至 $10800\ \mathrm s$。
      
      ---
      
      # 22. 基准计算参数
      
      | 项目 | 数值 |
      |---|---:|
      | 半径 $R$ | $0.02\ \mathrm m$ |
      | 长度 $L$ | $0.25\ \mathrm m$ |
      | 径向步长 $\Delta r$ | $5\times10^{-5}\ \mathrm m$ |
      | 径向节点数 | 401 |
      | 时间步长 $\Delta t$ | $0.5\ \mathrm s$ |
      | 计算时间范围 | $0\sim10800\ \mathrm s$ |
      | 空间离散 | 有限体积 |
      | 时间离散 | 后向欧拉 |
      | 界面物性 | 调和平均 |
      | 非线性迭代 | 同状态块 Picard |
      | 温度收敛阈值 | $10^{-8}\ ^\circ\mathrm C$ |
      | 水分收敛阈值 | $10^{-10}\ \mathrm{kg/kg}$ |
      | 单步最大 Picard 次数 | 50 |
      
      ---
      
      # 23. 初始状态下的特征量
      
      在
      
      $$
      C_0=2.55,
      \qquad
      T_0=28^\circ\mathrm C=301.15\ \mathrm K
      $$
      
      时：
      
      $$
      \rho_0
      =
      650+128\times2.55
      =
      976.4\ \mathrm{kg/m^3}.
      $$
      
      $$
      c_{p,0}
      =
      1450+
      2736\frac{2.55}{3.55}
      \approx3415.30\ \mathrm{J/(kg\,K)}.
      $$
      
      $$
      k_0
      =
      0.21+
      0.38\frac{2.55}{3.55}
      \approx0.48296\ \mathrm{W/(m\,K)}.
      $$
      
      水分扩散系数为
      
      $$
      D_0
      =
      2.4\times10^{-3}
      e^{-0.45/2.55}
      e^{-3850/301.15}
      \approx5.64\times10^{-9}\ \mathrm{m^2/s}.
      $$
      
      对应热扩散率
      
      $$
      \alpha_0
      =
      \frac{k_0}{\rho_0c_{p,0}}
      \approx
      1.45\times10^{-7}\ \mathrm{m^2/s}.
      $$
      
      二者比值约为
      
      $$
      \frac{\alpha_0}{D_0}
      \approx25.7.
      $$
      
      若用
      
      $$
      \tau\sim\frac{R^2}{\text{扩散系数}}
      $$
      
      估算特征时间，则初始热扩散特征时间约为
      
      $$
      \tau_T
      \approx
      \frac{(0.02)^2}{1.45\times10^{-7}}
      \approx
      2.76\times10^3\ \mathrm s
      \approx0.77\ \mathrm h,
      $$
      
      初始水分扩散特征时间约为
      
      $$
      \tau_C
      \approx
      \frac{(0.02)^2}{5.64\times10^{-9}}
      \approx
      7.09\times10^4\ \mathrm s
      \approx19.7\ \mathrm h.
      $$
      
      上述计算只基于初始状态，用于描述两个扩散过程在初始物性下的时间尺度量级；实际过程中 $\alpha$ 和 $D$ 会随 $T,C$ 变化。
      
      ---
      
      # 24. 模型对应的物理过程
      
      ## 24.1 热量传递过程
      
      表面对流换热通量为
      
      $$
      q_s
      =
      h
      \left(
      T_\infty-T_s
      \right).
      $$
      
      热量通过圆柱侧表面进入药材后，再由 Fourier 导热向内部传递。
      
      ---
      
      ## 24.2 水分迁移过程
      
      表面对流传质通量为
      
      $$
      J_s
      =
      h_m
      \left(
      C_s-C_\infty
      \right).
      $$
      
      内部水分通过 Fick 扩散由高含水率区域向低含水率区域迁移，并在表面与烘房环境发生交换。
      
      ---
      
      ## 24.3 状态耦合过程
      
      含水率通过
      
      $$
      \rho(C),\quad c_p(C),\quad k(C)
      $$
      
      改变温度方程中的储热能力和导热能力。
      
      温度和含水率共同通过
      
      $$
      D(T,C)
      $$
      
      改变水分扩散速度。
      
      因此温度场和水分场在每个时间步内通过材料物性的变化发生耦合。
      
      ---
      
      # 25. 数值验证项目
      
      ## 25.1 Picard 收敛检查
      
      对每个时间步记录
      
      $$
      \varepsilon_T,
      \qquad
      \varepsilon_C
      $$
      
      以及实际 Picard 迭代次数。
      
      所有正常接受的时间步均应满足预设收敛阈值。
      
      ---
      
      ## 25.2 时间步敏感性
      
      固定
      
      $$
      \Delta r=0.005\ \mathrm{cm},
      $$
      
      分别计算
      
      $$
      \Delta t=1\ \mathrm s
      $$
      
      和
      
      $$
      \Delta t=0.5\ \mathrm s.
      $$
      
      对题目表 3、表 4 所要求的时空位置计算
      
      $$
      E_T
      =
      \max
      \left|
      T_{\Delta t=1}
      -
      T_{\Delta t=0.5}
      \right|,
      $$
      
      $$
      E_C
      =
      \max
      \left|
      C_{\Delta t=1}
      -
      C_{\Delta t=0.5}
      \right|.
      $$
      
      该结果用于量化时间步变化对最终结果的影响。
      
      ---
      
      ## 25.3 空间网格敏感性
      
      固定
      
      $$
      \Delta t=0.5\ \mathrm s,
      $$
      
      分别计算
      
      $$
      \Delta r=0.01\ \mathrm{cm}
      $$
      
      和
      
      $$
      \Delta r=0.005\ \mathrm{cm}.
      $$
      
      计算题目关键时空位置上的最大差异：
      
      $$
      E_{T,r}
      =
      \max
      \left|
      T_{\Delta r=0.01}
      -
      T_{\Delta r=0.005}
      \right|,
      $$
      
      $$
      E_{C,r}
      =
      \max
      \left|
      C_{\Delta r=0.01}
      -
      C_{\Delta r=0.005}
      \right|.
      $$
      
      ---
      
      ## 25.4 基本数值检查
      
      计算结果应检查：
      
      1. $T,C$ 是否存在 NaN 或 Inf；
      2. $C$ 是否出现负值；
      3. 中心零通量条件是否满足；
      4. 表面热通量符号是否与 $T_\infty-T_s$ 一致；
      5. 表面水分通量符号是否与 $C_s-C_\infty$ 一致；
      6. 相邻时间步是否出现异常跳变；
      7. 离散方程残差是否处于线性求解器误差量级。
      
      这些检查用于判断数值计算过程是否满足所建立离散方程。
      
      ---
      
      # 26. 结果输出结构
      
      ## 26.1 表 3 温度
      
      提取时间
      
      $$
      t=
      0.5,\ 1.0,\ 1.5,\ 2.0,\ 2.5,\ 3.0\ \mathrm h
      $$
      
      和径向位置
      
      $$
      r=
      0,\ 0.5,\ 1.0,\ 1.5,\ 2.0\ \mathrm{cm}
      $$
      
      处的温度。
      
      ---
      
      ## 26.2 表 4 水分浓度
      
      在相同时间和径向位置提取
      
      $$
      C(r,t).
      $$
      
      ---
      
      ## 26.3 `result2.xlsx`
      
      完整输出采用：
      
      时间：
      
      $$
      0,1,2,\ldots,10800\ \mathrm s.
      $$
      
      径向距离：
      
      $$
      0,0.1,0.2,\ldots,2.0\ \mathrm{cm}.
      $$
      
      工作表结构：
      
      - `温度`
      - `水分浓度`
      
      A 列保存时间，单位 s。
      
      第一行保存到药材中心的距离，单位 cm。
      
      由于内部时间步为
      
      $$
      0.5\ \mathrm s,
      $$
      
      每两个内部时间步对应一个文件输出时刻。
      
      由于内部径向步长为
      
      $$
      0.005\ \mathrm{cm},
      $$
      
      题目要求的每隔 $0.1\ \mathrm{cm}$ 输出位置均落在计算节点上。
      
      ---
      
      # 27. 模型范围
      
      该模型包含：
      
      - 固定半径圆柱几何；
      - 一维径向温度场；
      - 一维径向水分场；
      - 附录 3 状态相关物性；
      - 表面对流换热；
      - 表面对流传质；
      - 时间变化的附件 1 环境边界；
      - 温度与水分通过物性形成的双向耦合。
      
      该模型不包含：
      
      - 药材半径收缩；
      - 移动网格；
      - 二维或三维空间效应；
      - 蒸发潜热项；
      - 辐射换热；
      - 多孔介质多相流；
      - 吸附等温线；
      - 水蒸气分压模型；
      - 轴向热质输运；
      - 附录 4 中的问题四物性公式。
      
      ---
      
      # 28. 数学模型汇总
      
      最终连续模型为
      
      $$
      \boxed{
      \rho(C)c_p(C)
      \frac{\partial T}{\partial t}
      =
      \frac{1}{r}
      \frac{\partial}{\partial r}
      \left[
      rk(C)\frac{\partial T}{\partial r}
      \right]
      }
      $$
      
      和
      
      $$
      \boxed{
      \frac{\partial C}{\partial t}
      =
      \frac{1}{r}
      \frac{\partial}{\partial r}
      \left[
      rD(T,C)\frac{\partial C}{\partial r}
      \right]
      }
      $$
      
      其中
      
      $$
      \rho=650+128C,
      $$
      
      $$
      c_p
      =
      1450+2736\frac{C}{C+1},
      $$
      
      $$
      k
      =
      0.21+0.38\frac{C}{C+1},
      $$
      
      $$
      D
      =
      2.4\times10^{-3}
      \exp\left(-\frac{0.45}{C}\right)
      \exp\left(-\frac{3850}{T+273.15}\right).
      $$
      
      初始条件：
      
      $$
      T(r,0)=28,
      \qquad
      C(r,0)=2.55.
      $$
      
      中心条件：
      
      $$
      \left.\frac{\partial T}{\partial r}\right|_{r=0}=0,
      \qquad
      \left.\frac{\partial C}{\partial r}\right|_{r=0}=0.
      $$
      
      表面条件：
      
      $$
      -k
      \left.\frac{\partial T}{\partial r}\right|_{r=R}
      =
      h(T_s-T_\infty),
      $$
      
      $$
      -D
      \left.\frac{\partial C}{\partial r}\right|_{r=R}
      =
      h_m(C_s-C_\infty).
      $$
      
      数值离散采用：
      
      $$
      \boxed{
      \text{圆柱径向有限体积}
      +
      \text{界面调和平均}
      +
      \text{后向欧拉}
      +
      \text{同状态块 Picard}
      }
      $$
      
      基准离散参数为
      
      $$
      \Delta r=0.005\ \mathrm{cm},
      \qquad
      \Delta t=0.5\ \mathrm s.
      $$
      
      最终数值结果需要通过本模型实际运行后得到，并据此重新计算时间步敏感性和空间网格敏感性。

## Activity

    $ /bin/zsh -lc "rg -n '"'^#'"' handoff/task2_handoff.md | tail -80 && sed -n '1000,1320p' handoff/task2_handoff.md && sed -n '1321,1700p' handoff/task2_handoff.md"
    status: Completed · exit 0
      1:# A题问题二：融合型温度—水分双向耦合全流程数学模型
      3:## 1. 问题定义
      51:## 2. 模型结构
      72:## 3. 模型假设
      122:## 4. 变量与参数
      144:## 5. 烘房环境边界数据
      186:## 6. 附录 3 状态相关物性
      264:## 7. 温度控制方程
      298:## 8. 水分控制方程
      327:## 9. 初始条件
      347:## 10. 中心轴边界条件
      369:## 11. 表面对流边界条件
      371:### 11.1 温度边界
      411:### 11.2 水分边界
      443:# 12. 空间离散
      445:## 12.1 径向有限体积网格
      493:## 12.2 控制体几何量
      537:# 13. 界面物性
      613:# 14. 时间离散
      653:# 15. 温度方程的有限体积离散
      728:# 16. 水分方程的有限体积离散
      801:# 17. 中心节点离散
      821:# 18. 表面节点离散
      823:## 18.1 温度表面节点
      868:## 18.2 水分表面节点
      911:# 19. 非线性耦合求解
      937:## 19.1 Picard 初值
      951:## 19.2 第 $m$ 次迭代
      1023:## 19.3 收敛判据
      1069:# 20. 三对角线性系统
      1107:# 21. 完整计算流程
      1152:# 22. 基准计算参数
      1172:# 23. 初始状态下的特征量
      1268:# 24. 模型对应的物理过程
      1270:## 24.1 热量传递过程
      1287:## 24.2 水分迁移过程
      1304:## 24.3 状态耦合过程
      1326:# 25. 数值验证项目
      1328:## 25.1 Picard 收敛检查
      1344:## 25.2 时间步敏感性
      1392:## 25.3 空间网格敏感性
      1438:## 25.4 基本数值检查
      1454:# 26. 结果输出结构
      1456:## 26.1 表 3 温度
      1476:## 26.2 表 4 水分浓度
      1486:## 26.3 `result2.xlsx`
      1529:# 27. 模型范围
      1557:# 28. 数学模型汇总
      T^n;
      \rho^{(m)},
      c_p^{(m)},
      k^{(m)}
      \right),
      $$
      
      $$
      C^{(m+1)}
      =
      \mathcal F_C
      \left(
      C^n;
      D^{(m)}
      \right).
      $$
      
      两场均求解完成后，共同进入下一轮物性更新。
      
      该过程持续到 $T,C$ 同时满足收敛条件。
      
      ---
      
      ## 19.3 收敛判据
      
      温度最大模变化量定义为
      
      $$
      \varepsilon_T^{(m)}
      =
      \max_i
      \left|
      T_i^{(m+1)}-T_i^{(m)}
      \right|.
      $$
      
      水分最大模变化量定义为
      
      $$
      \varepsilon_C^{(m)}
      =
      \max_i
      \left|
      C_i^{(m+1)}-C_i^{(m)}
      \right|.
      $$
      
      计算中可设置
      
      $$
      \varepsilon_T
      \le10^{-8}\ ^\circ\mathrm C,
      $$
      
      $$
      \varepsilon_C
      \le10^{-10}\ \mathrm{kg/kg}.
      $$
      
      单个时间步最大 Picard 迭代次数设置为
      
      $$
      50.
      $$
      
      若达到最大迭代次数仍未满足收敛条件，则记录该时间步为非线性迭代失败，不继续将该步视为正常收敛结果。
      
      ---
      
      # 20. 三对角线性系统
      
      无论温度方程还是水分方程，有限体积离散后都只涉及
      
      $$
      i-1,\quad i,\quad i+1
      $$
      
      三个相邻节点。
      
      因此矩阵形式为
      
      $$
      A\mathbf x=\mathbf b,
      $$
      
      其中 $A$ 为三对角矩阵。
      
      温度方程：
      
      $$
      A_T\mathbf T^{(m+1)}
      =
      \mathbf b_T.
      $$
      
      水分方程：
      
      $$
      A_C\mathbf C^{(m+1)}
      =
      \mathbf b_C.
      $$
      
      可采用三对角直接算法或带状矩阵直接求解器求解。
      
      ---
      
      # 21. 完整计算流程
      
      ```mermaid
      flowchart TD
          A["读取附件1"] --> B["构造 T∞(t), C∞(t) 分段线性插值"]
          B --> C["建立径向有限体积网格"]
          C --> D["设置 T(r,0)=28°C<br/>C(r,0)=2.55 kg/kg"]
          D --> E["进入时间步 n → n+1"]
          E --> F["T^(0)=T^n<br/>C^(0)=C^n"]
          F --> G["由 T^(m), C^(m)<br/>计算 ρ, cp, k, D"]
          G --> H["调和平均得到界面 k、D"]
          H --> I["组装温度三对角系统"]
          H --> J["组装水分三对角系统"]
          I --> K["求 T^(m+1)"]
          J --> L["求 C^(m+1)"]
          K --> M["检查 T、C Picard 收敛"]
          L --> M
          M -- "未收敛" --> G
          M -- "收敛" --> N["接受 T^(n+1), C^(n+1)"]
          N --> O["按输出时间保存结果"]
          O --> P{"t < 10800 s"}
          P -- "是" --> E
          P -- "否" --> Q["形成完整温度场和水分场"]
      ```
      
      对应计算顺序为：
      
      1. 读取附件 1；
      2. 构造 $T_\infty(t),C_\infty(t)$；
      3. 建立径向有限体积网格；
      4. 设置初始温度和含水率；
      5. 进入下一时间步；
      6. 使用上一时间层状态初始化 Picard；
      7. 根据当前 $T,C$ 更新 $\rho,c_p,k,D$；
      8. 计算界面调和平均；
      9. 组装温度和水分线性系统；
      10. 分别求解新的温度场和水分场；
      11. 判断 Picard 收敛；
      12. 未收敛则更新当前状态继续迭代；
      13. 收敛后接受新的时间层；
      14. 保存题目要求的时间和径向节点数据；
      15. 重复至 $10800\ \mathrm s$。
      
      ---
      
      # 22. 基准计算参数
      
      | 项目 | 数值 |
      |---|---:|
      | 半径 $R$ | $0.02\ \mathrm m$ |
      | 长度 $L$ | $0.25\ \mathrm m$ |
      | 径向步长 $\Delta r$ | $5\times10^{-5}\ \mathrm m$ |
      | 径向节点数 | 401 |
      | 时间步长 $\Delta t$ | $0.5\ \mathrm s$ |
      | 计算时间范围 | $0\sim10800\ \mathrm s$ |
      | 空间离散 | 有限体积 |
      | 时间离散 | 后向欧拉 |
      | 界面物性 | 调和平均 |
      | 非线性迭代 | 同状态块 Picard |
      | 温度收敛阈值 | $10^{-8}\ ^\circ\mathrm C$ |
      | 水分收敛阈值 | $10^{-10}\ \mathrm{kg/kg}$ |
      | 单步最大 Picard 次数 | 50 |
      
      ---
      
      # 23. 初始状态下的特征量
      
      在
      
      $$
      C_0=2.55,
      \qquad
      T_0=28^\circ\mathrm C=301.15\ \mathrm K
      $$
      
      时：
      
      $$
      \rho_0
      =
      650+128\times2.55
      =
      976.4\ \mathrm{kg/m^3}.
      $$
      
      $$
      c_{p,0}
      =
      1450+
      2736\frac{2.55}{3.55}
      \approx3415.30\ \mathrm{J/(kg\,K)}.
      $$
      
      $$
      k_0
      =
      0.21+
      0.38\frac{2.55}{3.55}
      \approx0.48296\ \mathrm{W/(m\,K)}.
      $$
      
      水分扩散系数为
      
      $$
      D_0
      =
      2.4\times10^{-3}
      e^{-0.45/2.55}
      e^{-3850/301.15}
      \approx5.64\times10^{-9}\ \mathrm{m^2/s}.
      $$
      
      对应热扩散率
      
      $$
      \alpha_0
      =
      \frac{k_0}{\rho_0c_{p,0}}
      \approx
      1.45\times10^{-7}\ \mathrm{m^2/s}.
      $$
      
      二者比值约为
      
      $$
      \frac{\alpha_0}{D_0}
      \approx25.7.
      $$
      
      若用
      
      $$
      \tau\sim\frac{R^2}{\text{扩散系数}}
      $$
      
      估算特征时间，则初始热扩散特征时间约为
      
      $$
      \tau_T
      \approx
      \frac{(0.02)^2}{1.45\times10^{-7}}
      \approx
      2.76\times10^3\ \mathrm s
      \approx0.77\ \mathrm h,
      $$
      
      初始水分扩散特征时间约为
      
      $$
      \tau_C
      \approx
      \frac{(0.02)^2}{5.64\times10^{-9}}
      \approx
      7.09\times10^4\ \mathrm s
      \approx19.7\ \mathrm h.
      $$
      
      上述计算只基于初始状态，用于描述两个扩散过程在初始物性下的时间尺度量级；实际过程中 $\alpha$ 和 $D$ 会随 $T,C$ 变化。
      
      ---
      
      # 24. 模型对应的物理过程
      
      ## 24.1 热量传递过程
      
      表面对流换热通量为
      
      $$
      q_s
      =
      h
      \left(
      T_\infty-T_s
      \right).
      $$
      
      热量通过圆柱侧表面进入药材后，再由 Fourier 导热向内部传递。
      
      ---
      
      ## 24.2 水分迁移过程
      
      表面对流传质通量为
      
      $$
      J_s
      =
      h_m
      \left(
      C_s-C_\infty
      \right).
      $$
      
      内部水分通过 Fick 扩散由高含水率区域向低含水率区域迁移，并在表面与烘房环境发生交换。
      
      ---
      
      ## 24.3 状态耦合过程
      
      含水率通过
      
      $$
      \rho(C),\quad c_p(C),\quad k(C)
      $$
      
      改变温度方程中的储热能力和导热能力。
      
      温度和含水率共同通过
      
      $$
      D(T,C)
      $$
      
      改变水分扩散速度。
      
      因此温度场和水分场在每个时间步内通过材料物性的变化发生耦合。
      
      ---
      
      # 25. 数值验证项目
      
      ## 25.1 Picard 收敛检查
      
      对每个时间步记录
      
      $$
      \varepsilon_T,
      \qquad
      \varepsilon_C
      $$
      
      以及实际 Picard 迭代次数。
      
      所有正常接受的时间步均应满足预设收敛阈值。
      
      ---
      
      ## 25.2 时间步敏感性
      
      固定
      
      $$
      \Delta r=0.005\ \mathrm{cm},
      $$
      
      分别计算
      
      $$
      \Delta t=1\ \mathrm s
      $$
      
      和
      
      $$
      \Delta t=0.5\ \mathrm s.
      $$
      
      对题目表 3、表 4 所要求的时空位置计算
      
      $$
      E_T
      =
      \max
      \left|
      T_{\Delta t=1}
      -
      T_{\Delta t=0.5}
      \right|,
      $$
      
      $$
      E_C
      =
      \max
      \left|
      C_{\Delta t=1}
      -
      C_{\Delta t=0.5}
      \right|.
      $$
      
      该结果用于量化时间步变化对最终结果的影响。
      
      ---
      
      ## 25.3 空间网格敏感性
      
      固定
      
      $$
      \Delta t=0.5\ \mathrm s,
      $$
      
      分别计算
      
      $$
      \Delta r=0.01\ \mathrm{cm}
      $$
      
      和
      
      $$
      \Delta r=0.005\ \mathrm{cm}.
      $$
      
      计算题目关键时空位置上的最大差异：
      
      $$
      E_{T,r}
      =
      \max
      \left|
      T_{\Delta r=0.01}
      -
      T_{\Delta r=0.005}
      \right|,
      $$
      
      $$
      E_{C,r}
      =
      \max
      \left|
      C_{\Delta r=0.01}
      -
      C_{\Delta r=0.005}
      \right|.
      $$
      
      ---
      
      ## 25.4 基本数值检查
      
      计算结果应检查：
      
      1. $T,C$ 是否存在 NaN 或 Inf；
      2. $C$ 是否出现负值；
      3. 中心零通量条件是否满足；
      4. 表面热通量符号是否与 $T_\infty-T_s$ 一致；
      5. 表面水分通量符号是否与 $C_s-C_\infty$ 一致；
      6. 相邻时间步是否出现异常跳变；
      7. 离散方程残差是否处于线性求解器误差量级。
      
      这些检查用于判断数值计算过程是否满足所建立离散方程。
      
      ---
      
      # 26. 结果输出结构
      
      ## 26.1 表 3 温度
      
      提取时间
      
      $$
      t=
      0.5,\ 1.0,\ 1.5,\ 2.0,\ 2.5,\ 3.0\ \mathrm h
      $$
      
      和径向位置
      
      $$
      r=
      0,\ 0.5,\ 1.0,\ 1.5,\ 2.0\ \mathrm{cm}
      $$
      
      处的温度。
      
      ---
      
      ## 26.2 表 4 水分浓度
      
      在相同时间和径向位置提取
      
      $$
      C(r,t).
      $$
      
      ---
      
      ## 26.3 `result2.xlsx`
      
      完整输出采用：
      
      时间：
      
      $$
      0,1,2,\ldots,10800\ \mathrm s.
      $$
      
      径向距离：
      
      $$
      0,0.1,0.2,\ldots,2.0\ \mathrm{cm}.
      $$
      
      工作表结构：
      
      - `温度`
      - `水分浓度`
      
      A 列保存时间，单位 s。
      
      第一行保存到药材中心的距离，单位 cm。
      
      由于内部时间步为
      
      $$
      0.5\ \mathrm s,
      $$
      
      每两个内部时间步对应一个文件输出时刻。
      
      由于内部径向步长为
      
      $$
      0.005\ \mathrm{cm},
      $$
      
      题目要求的每隔 $0.1\ \mathrm{cm}$ 输出位置均落在计算节点上。
      
      ---
      
      # 27. 模型范围
      
      该模型包含：
      
      - 固定半径圆柱几何；
      - 一维径向温度场；
      - 一维径向水分场；
      - 附录 3 状态相关物性；
      - 表面对流换热；
      - 表面对流传质；
      - 时间变化的附件 1 环境边界；
      - 温度与水分通过物性形成的双向耦合。
      
      该模型不包含：
      
      - 药材半径收缩；
      - 移动网格；
      - 二维或三维空间效应；
      - 蒸发潜热项；
      - 辐射换热；
      - 多孔介质多相流；
      - 吸附等温线；
      - 水蒸气分压模型；
      - 轴向热质输运；
      - 附录 4 中的问题四物性公式。
      
      ---
      
      # 28. 数学模型汇总
      
      最终连续模型为
      
      $$
      \boxed{
      \rho(C)c_p(C)
      \frac{\partial T}{\partial t}
      =
      \frac{1}{r}
      \frac{\partial}{\partial r}
      \left[
      rk(C)\frac{\partial T}{\partial r}
      \right]
      }
      $$
      
      和
      
      $$
      \boxed{
      \frac{\partial C}{\partial t}
      =
      \frac{1}{r}
      \frac{\partial}{\partial r}
      \left[
      rD(T,C)\frac{\partial C}{\partial r}
      \right]
      }
      $$
      
      其中
      
      $$
      \rho=650+128C,
      $$
      
      $$
      c_p
      =
      1450+2736\frac{C}{C+1},
      $$
      
      $$
      k
      =
      0.21+0.38\frac{C}{C+1},
      $$
      
      $$
      D
      =
      2.4\times10^{-3}
      \exp\left(-\frac{0.45}{C}\right)
      \exp\left(-\frac{3850}{T+273.15}\right).
      $$
      
      初始条件：
      
      $$
      T(r,0)=28,
      \qquad
      C(r,0)=2.55.
      $$
      
      中心条件：
      
      $$
      \left.\frac{\partial T}{\partial r}\right|_{r=0}=0,
      \qquad
      \left.\frac{\partial C}{\partial r}\right|_{r=0}=0.
      $$
      
      表面条件：
      
      $$
      -k
      \left.\frac{\partial T}{\partial r}\right|_{r=R}
      =
      h(T_s-T_\infty),
      $$
      
      $$
      -D
      \left.\frac{\partial C}{\partial r}\right|_{r=R}
      =
      h_m(C_s-C_\infty).
      $$
      
      数值离散采用：
      
      $$
      \boxed{
      \text{圆柱径向有限体积}
      +
      \text{界面调和平均}
      +
      \text{后向欧拉}
      +
      \text{同状态块 Picard}
      }
      $$
      
      基准离散参数为
      
      $$
      \Delta r=0.005\ \mathrm{cm},
      \qquad
      \Delta t=0.5\ \mathrm s.
      $$
      
      最终数值结果需要通过本模型实际运行后得到，并据此重新计算时间步敏感性和空间网格敏感性。

## Activity

    $ /bin/zsh -lc 'rg -n "BASE_DR_M|OUTPUT_DT_S|time_step_s:|face_k|face_D|time_step_s=|space|residual|Picard|harmonic|调和|算术" solution/task2/script/solve_task2.py && git log --oneline --all -- solution/task2 | head -12 && git status --short'
    status: Completed · exit 0
      4:问题二的 rho、cp、k、D 在每个时间步的 Picard 迭代中由当前 T、C 更新，
      27:BASE_DR_M = 0.000125
      31:OUTPUT_DT_S = 1.0
      38:# Picard 收敛参数。绝对阈值足以保证四位小数输出稳定，同时避免无意义地
      92:    radius_m: float = RADIUS_M, dr_m: float = BASE_DR_M
      101:    radii_m = np.linspace(0.0, radius_m, n_intervals + 1)
      113:    """按当前 Picard 状态计算 rho、cp、k 和 D（SI 单位）。"""
      134:    """解三对角线性系统，矩阵系数均为当前 Picard 冻结值。"""
      154:    """在给定 Picard 物性下求解一个后向欧拉温度步。"""
      160:    face_k = 0.5 * (conductivity[:-1] + conductivity[1:])
      161:    conductance = face_k * faces_m / dr_m
      186:    """在给定 Picard 物性下求解一个后向欧拉水分步。"""
      192:    face_D = 0.5 * (diffusivity[:-1] + diffusivity[1:])
      193:    conductance = face_D * faces_m / dr_m
      220:    """使用当前时间步内的 Picard 外迭代求 T、C 自洽解。"""
      260:                raise RuntimeError("Picard 步得到明显负水分浓度")
      272:        "问题二 Picard 迭代未收敛: "
      292:    time_step_s: float = 1.0,
      293:    output_dt_s: float = OUTPUT_DT_S,
      294:    dr_m: float = BASE_DR_M,
      417:        raise ValueError("Picard 迭代次数超出上限")
      533:        time_step_s=0.5,
      535:        dr_m=BASE_DR_M,
      598:    parser.add_argument("--output-dt", type=float, default=OUTPUT_DT_S)
      607:        f"dr={BASE_DR_M:g}m"
      612:        time_step_s=args.time_step,
      ed97452 修正问题二烘房边界数据
      94ffe31 修正问题二结果模板格式
      9375a01 生成问题二最终结果并完成数值验证
      e1db607 完成问题二三小时热质耦合求解
      a520f6d 完成问题二动态物性求解框架
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/

## Assistant

核对结论：`task2_handoff.md` 要求的优化不是普通性能调优，而是会改变最终数值场的基准离散升级。当前实现与 handoff 有三处差异：

1. 当前 `dr=0.000125 m`（161 节点）；handoff 要求 `dr=0.00005 m`（401 节点）。
2. 当前最终主解 `dt=1 s`；handoff 要求 `dt=0.5 s`，仍每 1 s 输出。
3. 当前界面 `k、D` 用算术平均；handoff 要求调和平均，并要求补充离散残差、时间步及空间网格敏感性验收。

推荐严格按 handoff 同时落实这三项，重新生成 CSV/XLSX 和表 3、表 4；模型方程、动态物性、附件1真实边界、Robin 条件和输出格式保持不变。

## Assistant

已确认采用严格 handoff 方案。`handoff/task2_handoff.md` 本身已是完整、已落盘的设计规格，因此不再创建重复设计文档；我会用 `writing-plans` 把它收敛为最短执行清单，然后交给 `luna-worker` 修改、重算和提交。

## Activity

    $ /bin/zsh -lc "sed -n '1,360p' /Users/jiaqiaosu/.agents/skills/writing-plans/SKILL.md"
    status: Completed · exit 0
      ---
      name: writing-plans
      description: Use when you have a spec or requirements for a multi-step task, before touching code
      ---
      
      # Writing Plans
      
      ## Overview
      
      Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.
      
      Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.
      
      **Announce at start:** "I'm using the writing-plans skill to create the implementation plan."
      
      **Context:** If working in an isolated worktree, it should have been created via the `superpowers:using-git-worktrees` skill at execution time.
      
      **Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
      - (User preferences for plan location override this default)
      
      ## Scope Check
      
      If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.
      
      ## File Structure
      
      Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.
      
      - Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
      - You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
      - Files that change together should live together. Split by responsibility, not by technical layer.
      - In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.
      
      This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.
      
      ## Bite-Sized Task Granularity
      
      **Each step is one action (2-5 minutes):**
      - "Write the failing test" - step
      - "Run it to make sure it fails" - step
      - "Implement the minimal code to make the test pass" - step
      - "Run the tests and make sure they pass" - step
      - "Commit" - step
      
      ## Plan Document Header
      
      **Every plan MUST start with this header:**
      
      ```markdown
      # [Feature Name] Implementation Plan
      
      > **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
      
      **Goal:** [One sentence describing what this builds]
      
      **Architecture:** [2-3 sentences about approach]
      
      **Tech Stack:** [Key technologies/libraries]
      
      ---
      ```
      
      ## Task Structure
      
      ````markdown
      ### Task N: [Component Name]
      
      **Files:**
      - Create: `exact/path/to/file.py`
      - Modify: `exact/path/to/existing.py:123-145`
      - Test: `tests/exact/path/to/test.py`
      
      - [ ] **Step 1: Write the failing test**
      
      ```python
      def test_specific_behavior():
          result = function(input)
          assert result == expected
      ```
      
      - [ ] **Step 2: Run test to verify it fails**
      
      Run: `pytest tests/path/test.py::test_name -v`
      Expected: FAIL with "function not defined"
      
      - [ ] **Step 3: Write minimal implementation**
      
      ```python
      def function(input):
          return expected
      ```
      
      - [ ] **Step 4: Run test to verify it passes**
      
      Run: `pytest tests/path/test.py::test_name -v`
      Expected: PASS
      
      - [ ] **Step 5: Commit**
      
      ```bash
      git add tests/path/test.py src/path/file.py
      git commit -m "feat: add specific feature"
      ```
      ````
      
      ## No Placeholders
      
      Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
      - "TBD", "TODO", "implement later", "fill in details"
      - "Add appropriate error handling" / "add validation" / "handle edge cases"
      - "Write tests for the above" (without actual test code)
      - "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
      - Steps that describe what to do without showing how (code blocks required for code steps)
      - References to types, functions, or methods not defined in any task
      
      ## Remember
      - Exact file paths always
      - Complete code in every step — if a step changes code, show the code
      - Exact commands with expected output
      - DRY, YAGNI, TDD, frequent commits
      
      ## Self-Review
      
      After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.
      
      **1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.
      
      **2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.
      
      **3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.
      
      If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.
      
      ## Execution Handoff
      
      After saving the plan, offer execution choice:
      
      **"Plan complete and saved to `docs/superpowers/plans/<filename>.md`. Two execution options:**
      
      **1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
      
      **2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints
      
      **Which approach?"**
      
      **If Subagent-Driven chosen:**
      - **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
      - Fresh subagent per task + two-stage review
      
      **If Inline Execution chosen:**
      - **REQUIRED SUB-SKILL:** Use superpowers:executing-plans
      - Batch execution with checkpoints for review

## Assistant

执行计划已收敛为一个版本，不创建额外文档：

1. 将基准网格改为 `dr=5×10⁻⁵ m`（401 节点），主时间步改为 `dt=0.5 s`，输出仍为每 1 s。
2. 将界面 `k、D` 从算术平均改为调和平均；Picard、方程、边界和物性公式不变。
3. 增加/启用线性残差、`dt=1 vs 0.5 s`、`dr=0.01 vs 0.005 cm` 验证。
4. 完整重算并覆盖 task2 的 CSV/XLSX，提取新表 3/4，中文提交。
5. root 复核代码差异、数值场、输出一致性与 commit。

下面执行表格编辑标记，然后委派 worker。

## Activity

    $ /bin/zsh -lc 'node container_tools/mark_artifact_operation_started.mjs --operation-kind edit --expected-output-count 1 --output-format xlsx'
    status: Completed · exit 0

## Activity

    Started `/root/optimize_task2_handoff`

## Activity

    agent tool: Wait · Completed

## Assistant

状态：worker 正在完成 401 节点、`dt=0.5 s` 和调和平均改造。计算量约为原最终主解的 5 倍以上，还需额外跑 `dt=1 s` 与粗网格对照；当前无阻塞。

## Activity

    agent tool: Wait · Completed

## Activity

    $ /bin/zsh -lc "git status --short --branch && git log --oneline -5 && git diff --stat -- solution/task2 && git diff -- solution/task2/script/solve_task2.py | sed -n '1,320p'"
    status: Completed · exit 0
      ## main...origin/main [ahead 3]
       M solution/task2/script/solve_task2.py
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/
      8af6846 更新问题三CN长期计算结果
      0f56894 完善问题三敏感性比较验证
      c0e35aa 重构问题三CN调和平均求解器
      959722d 优化了交接文档格式
      80c17df 补充任务三和任务四的上下文，以及部分任务四交接文档
       solution/task2/script/solve_task2.py | 49 ++++++++++++++++++++++++++++--------
       1 file changed, 39 insertions(+), 10 deletions(-)
      diff --git a/solution/task2/script/solve_task2.py b/solution/task2/script/solve_task2.py
      index effa9e6..5b1ffa9 100644
      --- a/solution/task2/script/solve_task2.py
      +++ b/solution/task2/script/solve_task2.py
      @@ -24,7 +24,7 @@ from scipy.linalg import solve_banded
       # 几何、初始状态和输出约定（内部长度统一使用 m）。
       RADIUS_M = 0.02
       LENGTH_M = 0.25  # 一维径向守恒式中约去，保留作题目参数记录。
      -BASE_DR_M = 0.000125
      +BASE_DR_M = 0.00005
       INITIAL_TEMPERATURE_C = 28.0
       INITIAL_MOISTURE_KGKG = 2.55
       FINAL_TIME_S = 10800.0
      @@ -40,6 +40,7 @@ MASS_TRANSFER_M_S = 8.0e-7
       PICARD_TOL_T_C = 1.0e-8
       PICARD_TOL_C_KGKG = 1.0e-10
       PICARD_MAX_ITER = 50
      +LINEAR_RESIDUAL_TOL = 1.0e-9
      
       DEFAULT_DATA_PATH = (
           Path(__file__).resolve().parents[3] / "problem" / "附件" / "附件1.xlsx"
      @@ -130,7 +131,7 @@ def material_properties(
      
       def _solve_tridiagonal(
           lower: np.ndarray, diagonal: np.ndarray, upper: np.ndarray, rhs: np.ndarray
      -) -> np.ndarray:
      +) -> tuple[np.ndarray, float]:
           """解三对角线性系统，矩阵系数均为当前 Picard 冻结值。"""
      
           n = diagonal.size
      @@ -138,7 +139,26 @@ def _solve_tridiagonal(
           banded[0, 1:] = upper
           banded[1, :] = diagonal
           banded[2, :-1] = lower
      -    return solve_banded((1, 1), banded, rhs, check_finite=False)
      +    solution = solve_banded((1, 1), banded, rhs, check_finite=False)
      +    residual = diagonal * solution - rhs
      +    if n > 1:
      +        residual[:-1] += upper * solution[1:]
      +        residual[1:] += lower * solution[:-1]
      +    scale = max(
      +        float(np.max(np.abs(rhs))),
      +        float(np.max(np.abs(diagonal * solution))),
      +        float(np.max(np.abs(upper * solution[1:]))) if n > 1 else 0.0,
      +        float(np.max(np.abs(lower * solution[:-1]))) if n > 1 else 0.0,
      +        1.0e-30,
      +    )
      +    normalized_residual = float(np.max(np.abs(residual)) / scale)
      +    if not np.isfinite(normalized_residual) or normalized_residual > LINEAR_RESIDUAL_TOL:
      +        raise RuntimeError(
      +            "三对角线性系统残差异常: "
      +            f"normalized_inf_residual={normalized_residual:.3e}, "
      +            f"tol={LINEAR_RESIDUAL_TOL:.3e}"
      +        )
      +    return solution, normalized_residual
      
      
       def _solve_temperature_linear(
      @@ -150,14 +170,16 @@ def _solve_temperature_linear(
           dr_m: float,
           dt_s: float,
           air_temperature_C: float,
      -) -> np.ndarray:
      +) -> tuple[np.ndarray, float]:
           """在给定 Picard 物性下求解一个后向欧拉温度步。"""
      
           rho, cp, conductivity, _ = material_properties(
               guess_temperature_C, guess_moisture_kgkg
           )
           storage = rho * cp * radial_measure_m2
      -    face_k = 0.5 * (conductivity[:-1] + conductivity[1:])
      +    face_k = 2.0 * conductivity[:-1] * conductivity[1:] / (
      +        conductivity[:-1] + conductivity[1:]
      +    )
           conductance = face_k * faces_m / dr_m
      
           diagonal = storage.copy()
      @@ -182,14 +204,16 @@ def _solve_moisture_linear(
           dr_m: float,
           dt_s: float,
           air_moisture_kgkg: float,
      -) -> np.ndarray:
      +) -> tuple[np.ndarray, float]:
           """在给定 Picard 物性下求解一个后向欧拉水分步。"""
      
           _, _, _, diffusivity = material_properties(
               guess_temperature_C, guess_moisture_kgkg
           )
           storage = radial_measure_m2
      -    face_D = 0.5 * (diffusivity[:-1] + diffusivity[1:])
      +    face_D = 2.0 * diffusivity[:-1] * diffusivity[1:] / (
      +        diffusivity[:-1] + diffusivity[1:]
      +    )
           conductance = face_D * faces_m / dr_m
      
           diagonal = storage.copy()
      @@ -216,7 +240,7 @@ def _picard_step(
           tol_temperature_C: float = PICARD_TOL_T_C,
           tol_moisture_kgkg: float = PICARD_TOL_C_KGKG,
           max_iter: int = PICARD_MAX_ITER,
      -) -> tuple[np.ndarray, np.ndarray, int, float, float]:
      +) -> tuple[np.ndarray, np.ndarray, int, float, float, float]:
           """使用当前时间步内的 Picard 外迭代求 T、C 自洽解。"""
      
           # time_new_s 同时用于异常信息，明确边界取值属于当前时间步。
      @@ -224,9 +248,10 @@ def _picard_step(
           guess_moisture_kgkg = old_moisture_kgkg.copy()
           last_delta_temperature = np.inf
           last_delta_moisture = np.inf
      +    max_linear_residual = 0.0
      
           for iteration in range(1, max_iter + 1):
      -        new_temperature_C = _solve_temperature_linear(
      +        new_temperature_C, temperature_residual = _solve_temperature_linear(
                   old_temperature_C,
                   guess_temperature_C,
                   guess_moisture_kgkg,
      @@ -236,7 +261,7 @@ def _picard_step(
                   dt_s,
                   air_temperature_C,
               )
      -        new_moisture_kgkg = _solve_moisture_linear(
      +        new_moisture_kgkg, moisture_residual = _solve_moisture_linear(
                   old_moisture_kgkg,
                   guess_temperature_C,
                   guess_moisture_kgkg,
      @@ -246,6 +271,9 @@ def _picard_step(
                   dt_s,
                   air_moisture_kgkg,
               )
      +        max_linear_residual = max(
      +            max_linear_residual, temperature_residual, moisture_residual
      +        )
               last_delta_temperature = float(
                   np.max(np.abs(new_temperature_C - guess_temperature_C))
               )
      @@ -264,6 +292,7 @@ def _picard_step(
                       iteration,
                       last_delta_temperature,
                       last_delta_moisture,
      +                max_linear_residual,
                   )
               guess_temperature_C = new_temperature_C
               guess_moisture_kgkg = new_moisture_kgkg

## Activity

    agent tool: Wait · Completed

## Activity

    Interacted with `/root/optimize_task2_handoff`

## Activity

    agent tool: Wait · Completed

## Assistant

状态：代码层面的 handoff 差异已落地，包含 401 节点、调和平均和真实线性残差计算。worker 当前仍在长时间数值运行/验证阶段；我正在确认是正常计算耗时还是某个验证路径重复计算，不会在没有证据时改代码。

## Activity

    $ /bin/zsh -lc "stat -f '%Sm %z %N' solution/task2/script/solve_task2.py solution/task2/answer/result2.xlsx solution/task2/answer/task2_all_results.csv && git status --short"
    status: Completed · exit 0
      Sep 11 12:00:46 2026 36742 solution/task2/script/solve_task2.py
      Sep 11 12:01:18 2026 2468585 solution/task2/answer/result2.xlsx
      Sep 11 12:01:19 2026 7705478 solution/task2/answer/task2_all_results.csv
       M solution/task2/answer/result2.xlsx
       M solution/task2/answer/task2_all_results.csv
       M solution/task2/script/solve_task2.py
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/

## Activity

    agent tool: Wait · Completed

## Activity

    Interacted with `/root/optimize_task2_handoff`

## Activity

    agent tool: Wait · Completed

## Assistant

worker 已完成输出生成，但后续验收/提交阶段异常延长，极可能卡在大文件差异或重复全量检查。我将中断当前卡住的 turn，再让同一 worker 从现有文件继续做轻量验收和提交，不重新开始求解。

## Activity

    Interrupted `/root/optimize_task2_handoff`

## Activity

    Interacted with `/root/optimize_task2_handoff`

## Activity

    agent tool: Wait · Completed

## Activity

    Completed `/root/optimize_task2_handoff`

## Activity

    agent tool: Wait · Completed

## Assistant

worker 已完成并提交 `9499d02`。优化后的关键变化量很小（相对上一版关键点温度最大 `0.0008 °C`、水分最大 `0.0001 kg/kg`），说明原结果已接近收敛；但当前版本现在严格符合 handoff 的基准离散。接下来由 root 做最终独立验收，不依据 worker 自报直接结束。

## Activity

    $ /bin/zsh -lc "git status --short --branch && git show --stat --oneline 9499d02 && git show --name-only --format='' 9499d02 && git diff --check 9499d02"'^..9499d02 && git diff 9499d02''^..9499d02 -- solution/task2/script/solve_task2.py | sed -n '"'1,520p' && rg -n \"BASE_DR_M|time_step_s:|parser.add_argument\\(\\\"--time-step|face_k|face_D|normalized_residual|time_step_sensitivity|space_grid_sensitivity|linear_residual\" solution/task2/script/solve_task2.py"
    status: Completed · exit 0
      diff --git a/solution/task2/script/solve_task2.py b/solution/task2/script/solve_task2.py
      index effa9e6..dbb0eca 100644
      --- a/solution/task2/script/solve_task2.py
      +++ b/solution/task2/script/solve_task2.py
      @@ -24,7 +24,7 @@ from scipy.linalg import solve_banded
       # 几何、初始状态和输出约定（内部长度统一使用 m）。
       RADIUS_M = 0.02
       LENGTH_M = 0.25  # 一维径向守恒式中约去，保留作题目参数记录。
      -BASE_DR_M = 0.000125
      +BASE_DR_M = 0.00005
       INITIAL_TEMPERATURE_C = 28.0
       INITIAL_MOISTURE_KGKG = 2.55
       FINAL_TIME_S = 10800.0
      @@ -40,6 +40,7 @@ MASS_TRANSFER_M_S = 8.0e-7
       PICARD_TOL_T_C = 1.0e-8
       PICARD_TOL_C_KGKG = 1.0e-10
       PICARD_MAX_ITER = 50
      +LINEAR_RESIDUAL_TOL = 1.0e-9
      
       DEFAULT_DATA_PATH = (
           Path(__file__).resolve().parents[3] / "problem" / "附件" / "附件1.xlsx"
      @@ -128,9 +129,27 @@ def material_properties(
           return rho, cp, k, diffusivity
      
      
      +def _harmonic_mean_positive(
      +    left: np.ndarray, right: np.ndarray, name: str
      +) -> np.ndarray:
      +    """计算严格正值数组的界面调和平均。"""
      +
      +    if (
      +        np.any(~np.isfinite(left))
      +        or np.any(~np.isfinite(right))
      +        or np.any(left <= 0.0)
      +        or np.any(right <= 0.0)
      +    ):
      +        raise ValueError(f"{name} 界面调和平均要求两侧物性均为有限正值")
      +    result = 2.0 * left * right / (left + right)
      +    if np.any(~np.isfinite(result)) or np.any(result <= 0.0):
      +        raise ValueError(f"{name} 界面调和平均未得到严格正值")
      +    return result
      +
      +
       def _solve_tridiagonal(
           lower: np.ndarray, diagonal: np.ndarray, upper: np.ndarray, rhs: np.ndarray
      -) -> np.ndarray:
      +) -> tuple[np.ndarray, float]:
           """解三对角线性系统，矩阵系数均为当前 Picard 冻结值。"""
      
           n = diagonal.size
      @@ -138,7 +157,26 @@ def _solve_tridiagonal(
           banded[0, 1:] = upper
           banded[1, :] = diagonal
           banded[2, :-1] = lower
      -    return solve_banded((1, 1), banded, rhs, check_finite=False)
      +    solution = solve_banded((1, 1), banded, rhs, check_finite=False)
      +    residual = diagonal * solution - rhs
      +    if n > 1:
      +        residual[:-1] += upper * solution[1:]
      +        residual[1:] += lower * solution[:-1]
      +    scale = max(
      +        float(np.max(np.abs(rhs))),
      +        float(np.max(np.abs(diagonal * solution))),
      +        float(np.max(np.abs(upper * solution[1:]))) if n > 1 else 0.0,
      +        float(np.max(np.abs(lower * solution[:-1]))) if n > 1 else 0.0,
      +        1.0e-30,
      +    )
      +    normalized_residual = float(np.max(np.abs(residual)) / scale)
      +    if not np.isfinite(normalized_residual) or normalized_residual > LINEAR_RESIDUAL_TOL:
      +        raise RuntimeError(
      +            "三对角线性系统残差异常: "
      +            f"normalized_inf_residual={normalized_residual:.3e}, "
      +            f"tol={LINEAR_RESIDUAL_TOL:.3e}"
      +        )
      +    return solution, normalized_residual
      
      
       def _solve_temperature_linear(
      @@ -150,14 +188,14 @@ def _solve_temperature_linear(
           dr_m: float,
           dt_s: float,
           air_temperature_C: float,
      -) -> np.ndarray:
      +) -> tuple[np.ndarray, float]:
           """在给定 Picard 物性下求解一个后向欧拉温度步。"""
      
           rho, cp, conductivity, _ = material_properties(
               guess_temperature_C, guess_moisture_kgkg
           )
           storage = rho * cp * radial_measure_m2
      -    face_k = 0.5 * (conductivity[:-1] + conductivity[1:])
      +    face_k = _harmonic_mean_positive(conductivity[:-1], conductivity[1:], "导热系数")
           conductance = face_k * faces_m / dr_m
      
           diagonal = storage.copy()
      @@ -182,14 +220,14 @@ def _solve_moisture_linear(
           dr_m: float,
           dt_s: float,
           air_moisture_kgkg: float,
      -) -> np.ndarray:
      +) -> tuple[np.ndarray, float]:
           """在给定 Picard 物性下求解一个后向欧拉水分步。"""
      
           _, _, _, diffusivity = material_properties(
               guess_temperature_C, guess_moisture_kgkg
           )
           storage = radial_measure_m2
      -    face_D = 0.5 * (diffusivity[:-1] + diffusivity[1:])
      +    face_D = _harmonic_mean_positive(diffusivity[:-1], diffusivity[1:], "扩散系数")
           conductance = face_D * faces_m / dr_m
      
           diagonal = storage.copy()
      @@ -216,7 +254,7 @@ def _picard_step(
           tol_temperature_C: float = PICARD_TOL_T_C,
           tol_moisture_kgkg: float = PICARD_TOL_C_KGKG,
           max_iter: int = PICARD_MAX_ITER,
      -) -> tuple[np.ndarray, np.ndarray, int, float, float]:
      +) -> tuple[np.ndarray, np.ndarray, int, float, float, float]:
           """使用当前时间步内的 Picard 外迭代求 T、C 自洽解。"""
      
           # time_new_s 同时用于异常信息，明确边界取值属于当前时间步。
      @@ -224,9 +262,10 @@ def _picard_step(
           guess_moisture_kgkg = old_moisture_kgkg.copy()
           last_delta_temperature = np.inf
           last_delta_moisture = np.inf
      +    max_linear_residual = 0.0
      
           for iteration in range(1, max_iter + 1):
      -        new_temperature_C = _solve_temperature_linear(
      +        new_temperature_C, temperature_residual = _solve_temperature_linear(
                   old_temperature_C,
                   guess_temperature_C,
                   guess_moisture_kgkg,
      @@ -236,7 +275,7 @@ def _picard_step(
                   dt_s,
                   air_temperature_C,
               )
      -        new_moisture_kgkg = _solve_moisture_linear(
      +        new_moisture_kgkg, moisture_residual = _solve_moisture_linear(
                   old_moisture_kgkg,
                   guess_temperature_C,
                   guess_moisture_kgkg,
      @@ -246,6 +285,9 @@ def _picard_step(
                   dt_s,
                   air_moisture_kgkg,
               )
      +        max_linear_residual = max(
      +            max_linear_residual, temperature_residual, moisture_residual
      +        )
               last_delta_temperature = float(
                   np.max(np.abs(new_temperature_C - guess_temperature_C))
               )
      @@ -264,6 +306,7 @@ def _picard_step(
                       iteration,
                       last_delta_temperature,
                       last_delta_moisture,
      +                max_linear_residual,
                   )
               guess_temperature_C = new_temperature_C
               guess_moisture_kgkg = new_moisture_kgkg
      @@ -289,7 +332,7 @@ def _output_indices(radii_m: np.ndarray) -> np.ndarray:
       def solve_task2(
           data_path: str | Path = DEFAULT_DATA_PATH,
           t_end_s: float = FINAL_TIME_S,
      -    time_step_s: float = 1.0,
      +    time_step_s: float = 0.5,
           output_dt_s: float = OUTPUT_DT_S,
           dr_m: float = BASE_DR_M,
           progress: bool = False,
      @@ -321,6 +364,8 @@ def solve_task2(
           output_times = output_dt_s * np.arange(n_outputs_total, dtype=float)
           temperature_output = np.empty((n_outputs_total, output_indices.size), dtype=float)
           moisture_output = np.empty_like(temperature_output)
      +    air_temperature_output = np.interp(output_times, air_time_s, air_temperature)
      +    air_moisture_output = np.interp(output_times, air_time_s, air_moisture)
           initial_temperature = np.full(n_nodes, INITIAL_TEMPERATURE_C, dtype=float)
           initial_moisture = np.full(n_nodes, INITIAL_MOISTURE_KGKG, dtype=float)
           current_temperature = initial_temperature.copy()
      @@ -330,6 +375,7 @@ def solve_task2(
           iteration_counts = np.empty(n_steps, dtype=int)
           picard_delta_temperature = np.empty(n_steps, dtype=float)
           picard_delta_moisture = np.empty(n_steps, dtype=float)
      +    linear_residuals = np.empty(n_steps, dtype=float)
           air_temperature_interp = lambda t: float(np.interp(t, air_time_s, air_temperature))
           air_moisture_interp = lambda t: float(np.interp(t, air_time_s, air_moisture))
      
      @@ -341,6 +387,7 @@ def solve_task2(
                   iteration_counts[step - 1],
                   picard_delta_temperature[step - 1],
                   picard_delta_moisture[step - 1],
      +            linear_residuals[step - 1],
               ) = _picard_step(
                   current_temperature,
                   current_moisture,
      @@ -364,12 +411,18 @@ def solve_task2(
               "radius_cm": OUTPUT_RADIUS_CM.copy(),
               "temperature_C": temperature_output,
               "moisture_kgkg": moisture_output,
      +        "air_temperature_C": air_temperature_output,
      +        "air_moisture_kgkg": air_moisture_output,
               "radius_m_internal": radii_m,
               "time_step_s": float(time_step_s),
               "dr_m": float(dr_m),
               "iteration_counts": iteration_counts,
               "picard_delta_temperature": picard_delta_temperature,
               "picard_delta_moisture": picard_delta_moisture,
      +        "linear_residuals": linear_residuals,
      +        "max_linear_residual": float(np.max(linear_residuals)) if n_steps else 0.0,
      +        "center_inner_face_radius_m": float(0.0),
      +        "center_inner_boundary_coefficient": float(0.0),
               "air_temperature_last_C": air_temperature_interp(t_end_s),
               "air_moisture_last_kgkg": air_moisture_interp(t_end_s),
           }
      @@ -382,20 +435,34 @@ def validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
           radius_cm = np.asarray(solution["radius_cm"], dtype=float)
           temperature = np.asarray(solution["temperature_C"], dtype=float)
           moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
      +    air_temperature = np.asarray(solution["air_temperature_C"], dtype=float)
      +    air_moisture = np.asarray(solution["air_moisture_kgkg"], dtype=float)
      +    if time_s.size != 10801 or radius_cm.size != 21:
      +        raise ValueError("完整结果必须为 10801 个时间点和 21 个半径点")
           if temperature.shape != (time_s.size, radius_cm.size):
               raise ValueError("温度输出数组形状错误")
           if moisture.shape != temperature.shape:
               raise ValueError("温度和水分输出数组形状不一致")
      +    if air_temperature.shape != time_s.shape or air_moisture.shape != time_s.shape:
      +        raise ValueError("烘房边界输出数组形状错误")
           if not np.all(np.isfinite(np.column_stack((temperature.ravel(), moisture.ravel())))):
               raise ValueError("结果包含 NaN 或 Inf")
      +    if not np.all(np.isfinite(np.column_stack((air_temperature, air_moisture)))):
      +        raise ValueError("烘房边界结果包含 NaN 或 Inf")
           if np.min(moisture) < -1.0e-10:
               raise ValueError(f"结果包含负水分浓度: min={np.min(moisture):.6g}")
      -    if not np.isclose(temperature[0, 0], INITIAL_TEMPERATURE_C, atol=1.0e-12):
      -        raise ValueError("初始中心温度不符合题设")
      -    if not np.isclose(moisture[0, 0], INITIAL_MOISTURE_KGKG, atol=1.0e-12):
      -        raise ValueError("初始中心水分不符合题设")
      +    if not np.allclose(temperature[0], INITIAL_TEMPERATURE_C, atol=1.0e-12):
      +        raise ValueError("初始全径向温度不符合题设")
      +    if not np.allclose(moisture[0], INITIAL_MOISTURE_KGKG, atol=1.0e-12):
      +        raise ValueError("初始全径向水分不符合题设")
      +    if not np.isclose(time_s[0], 0.0, atol=1.0e-12) or not np.isclose(
      +        time_s[-1], FINAL_TIME_S, atol=1.0e-10
      +    ):
      +        raise ValueError("结果时间范围必须完整覆盖 0--10800 s")
           if not np.all(np.diff(time_s) > 0.0):
               raise ValueError("输出时间没有严格递增")
      +    if not np.allclose(np.diff(time_s), OUTPUT_DT_S, atol=1.0e-10):
      +        raise ValueError("输出时间间隔不是 1 s")
           if not np.isclose(radius_cm[0], 0.0) or not np.isclose(radius_cm[-1], 2.0):
               raise ValueError("输出半径范围不符合 0--2 cm")
      
      @@ -412,9 +479,43 @@ def validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
           if np.max(np.abs(np.diff(moisture, axis=0))) > 0.2:
               raise ValueError("相邻输出时刻水分出现明显跳变")
      
      +    heat_boundary_driver = air_temperature - temperature[:, -1]
      +    moisture_boundary_driver = air_moisture - moisture[:, -1]
      +    heat_inward_fraction = float(np.mean(heat_boundary_driver[1:] >= -1.0e-8))
      +    moisture_outward_fraction = float(np.mean(moisture_boundary_driver[1:] <= 1.0e-8))
      +    if heat_boundary_driver[1] < -1.0e-8 or heat_boundary_driver[-1] < -1.0e-8:
      +        raise ValueError("表面热边界方向异常：起始或末时刻未体现烘房向药材传热")
      +    if moisture_boundary_driver[1] > 1.0e-8 or moisture_boundary_driver[-1] > 1.0e-8:
      +        raise ValueError("表面传质边界方向异常：起始或末时刻未体现药材向外失水")
      +    if heat_inward_fraction < 0.95 or moisture_outward_fraction < 0.95:
      +        raise ValueError("表面边界方向异常：主导时段未体现热进入、水分流出")
      +
           iterations = np.asarray(solution["iteration_counts"], dtype=int)
           if iterations.size and np.max(iterations) > PICARD_MAX_ITER:
               raise ValueError("Picard 迭代次数超出上限")
      +    picard_delta_temperature = np.asarray(
      +        solution["picard_delta_temperature"], dtype=float
      +    )
      +    picard_delta_moisture = np.asarray(solution["picard_delta_moisture"], dtype=float)
      +    linear_residuals = np.asarray(solution["linear_residuals"], dtype=float)
      +    if (
      +        picard_delta_temperature.shape != iterations.shape
      +        or picard_delta_moisture.shape != iterations.shape
      +        or linear_residuals.shape != iterations.shape
      +    ):
      +        raise ValueError("Picard 或线性残差记录长度错误")
      +    if not np.all(np.isfinite(linear_residuals)) or np.max(linear_residuals) > LINEAR_RESIDUAL_TOL:
      +        raise ValueError("三对角线性系统残差超过容差")
      +    if np.any(picard_delta_temperature > PICARD_TOL_T_C) or np.any(
      +        picard_delta_moisture > PICARD_TOL_C_KGKG
      +    ):
      +        raise ValueError("存在未达到收敛阈值的 Picard 时间步")
      +    center_face_radius = float(solution["center_inner_face_radius_m"])
      +    center_boundary_coefficient = float(solution["center_inner_boundary_coefficient"])
      +    if not np.isclose(center_face_radius, 0.0, atol=1.0e-15) or not np.isclose(
      +        center_boundary_coefficient, 0.0, atol=1.0e-30
      +    ):
      +        raise ValueError("中心内侧控制面未体现零通量离散")
           return {
               "time_end_s": float(time_s[-1]),
               "temperature_min_C": float(np.min(temperature)),
      @@ -423,9 +524,23 @@ def validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
               "moisture_max_kgkg": float(np.max(moisture)),
               "max_picard_iterations": int(np.max(iterations)) if iterations.size else 0,
               "mean_picard_iterations": float(np.mean(iterations)) if iterations.size else 0.0,
      +        "max_linear_residual": float(np.max(linear_residuals))
      +        if linear_residuals.size
      +        else 0.0,
               "center_surface_temperature_gap_C": float(final_temperature[-1] - final_temperature[0]),
               "center_surface_moisture_gap_kgkg": float(final_moisture[0] - final_moisture[-1]),
      -        "center_flux_zero_discretisation": True,
      +        "center_inner_face_radius_m": center_face_radius,
      +        "center_inner_boundary_coefficient": center_boundary_coefficient,
      +        "center_flux_zero_discretisation": bool(
      +            np.isclose(center_face_radius, 0.0, atol=1.0e-15)
      +            and np.isclose(center_boundary_coefficient, 0.0, atol=1.0e-30)
      +        ),
      +        "minimum_heat_boundary_driver_C": float(np.min(heat_boundary_driver[1:])),
      +        "heat_inward_fraction": heat_inward_fraction,
      +        "maximum_moisture_boundary_driver_kgkg": float(
      +            np.max(moisture_boundary_driver[1:])
      +        ),
      +        "moisture_outward_fraction": moisture_outward_fraction,
           }
      
      
      @@ -521,42 +636,128 @@ def key_tables(solution: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.nda
           return target_times, temperature, moisture
      
      
      +def _key_point_values(
      +    solution: dict[str, Any],
      +) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
      +    """提取表3/表4的时间和五个关键径向位置。"""
      +
      +    target_times = np.array([1800, 3600, 5400, 7200, 9000, 10800], dtype=float)
      +    time_s = np.asarray(solution["time_s"], dtype=float)
      +    time_indices = np.array(
      +        [int(np.argmin(np.abs(time_s - target))) for target in target_times]
      +    )
      +    if not np.allclose(time_s[time_indices], target_times, atol=1.0e-10):
      +        raise ValueError("完整结果中缺少敏感性检查要求的时间点")
      +    key_radius_indices = np.array([0, 5, 10, 15, 20], dtype=int)
      +    return (
      +        target_times,
      +        OUTPUT_RADIUS_CM[key_radius_indices],
      +        np.asarray(solution["temperature_C"])[
      +            time_indices[:, None], key_radius_indices[None, :]
      +        ],
      +        np.asarray(solution["moisture_kgkg"])[
      +            time_indices[:, None], key_radius_indices[None, :]
      +        ],
      +    )
      +
      +
       def time_step_sensitivity(
      -    base_solution: dict[str, Any],
      +    base_solution: dict[str, Any] | None = None,
           data_path: str | Path = DEFAULT_DATA_PATH,
       ) -> dict[str, Any]:
      -    """比较 dt=1 s 与 dt=0.5 s 在表3/表4点的差异。"""
      -
      -    fine_solution = solve_task2(
      +    """以最终 dt=0.5 s 为基准，比较 dt=1 s 在表3/表4点的差异。"""
      +
      +    if base_solution is not None and np.isclose(
      +        float(base_solution["time_step_s"]), 0.5
      +    ) and np.isclose(float(base_solution["dr_m"]), BASE_DR_M):
      +        reference_solution = base_solution
      +    else:
      +        reference_solution = solve_task2(
      +            data_path=data_path,
      +            t_end_s=FINAL_TIME_S,
      +            time_step_s=0.5,
      +            output_dt_s=1.0,
      +            dr_m=BASE_DR_M,
      +            progress=True,
      +        )
      +    comparison_solution = solve_task2(
               data_path=data_path,
               t_end_s=FINAL_TIME_S,
      -        time_step_s=0.5,
      +        time_step_s=1.0,
               output_dt_s=1.0,
               dr_m=BASE_DR_M,
               progress=True,
           )
      -    key_times_s = np.array([1800, 3600, 5400, 7200, 9000, 10800], dtype=float)
      -    key_radius_indices = np.array([0, 5, 10, 15, 20], dtype=int)
      -    base_time_indices = np.array(
      -        [int(np.argmin(np.abs(np.asarray(base_solution["time_s"]) - t))) for t in key_times_s]
      +    validate_solution(comparison_solution)
      +    key_times_s, key_radius_cm, reference_temperature, reference_moisture = (
      +        _key_point_values(reference_solution)
           )
      -    fine_time_indices = np.array(
      -        [int(np.argmin(np.abs(np.asarray(fine_solution["time_s"]) - t))) for t in key_times_s]
      +    _, _, comparison_temperature, comparison_moisture = _key_point_values(
      +        comparison_solution
           )
      -    base_temperature = np.asarray(base_solution["temperature_C"])[
      -        base_time_indices[:, None], key_radius_indices[None, :]
      -    ]
      -    fine_temperature = np.asarray(fine_solution["temperature_C"])[
      -        fine_time_indices[:, None], key_radius_indices[None, :]
      -    ]
      -    base_moisture = np.asarray(base_solution["moisture_kgkg"])[
      -        base_time_indices[:, None], key_radius_indices[None, :]
      -    ]
      -    fine_moisture = np.asarray(fine_solution["moisture_kgkg"])[
      -        fine_time_indices[:, None], key_radius_indices[None, :]
      -    ]
      -    temperature_difference = np.abs(fine_temperature - base_temperature)
      -    moisture_difference = np.abs(fine_moisture - base_moisture)
      +    temperature_difference = np.abs(comparison_temperature - reference_temperature)
      +    moisture_difference = np.abs(comparison_moisture - reference_moisture)
      +    temperature_position = np.unravel_index(
      +        int(np.argmax(temperature_difference)), temperature_difference.shape
      +    )
      +    moisture_position = np.unravel_index(
      +        int(np.argmax(moisture_difference)), moisture_difference.shape
      +    )
      +    return {
      +        "reference_solution": reference_solution,
      +        "comparison_solution": comparison_solution,
      +        "reference_time_step_s": 0.5,
      +        "comparison_time_step_s": 1.0,
      +        "dr_m": BASE_DR_M,
      +        "key_times_s": key_times_s,
      +        "key_radius_cm": key_radius_cm,
      +        "temperature_max_abs_difference_C": float(np.max(temperature_difference)),
      +        "temperature_difference_position": (
      +            float(key_times_s[temperature_position[0]]),
      +            float(key_radius_cm[temperature_position[1]]),
      +        ),
      +        "moisture_max_abs_difference_kgkg": float(np.max(moisture_difference)),
      +        "moisture_difference_position": (
      +            float(key_times_s[moisture_position[0]]),
      +            float(key_radius_cm[moisture_position[1]]),
      +        ),
      +    }
      +
      +
      +def space_grid_sensitivity(
      +    base_solution: dict[str, Any] | None = None,
      +    data_path: str | Path = DEFAULT_DATA_PATH,
      +) -> dict[str, Any]:
      +    """以 dt=0.5 s 为基准，比较 dr=0.01 cm 与 0.005 cm。"""
      +
      +    if base_solution is not None and np.isclose(
      +        float(base_solution["time_step_s"]), 0.5
      +    ) and np.isclose(float(base_solution["dr_m"]), BASE_DR_M):
      +        fine_solution = base_solution
      +    else:
      +        fine_solution = solve_task2(
      +            data_path=data_path,
      +            t_end_s=FINAL_TIME_S,
      +            time_step_s=0.5,
      +            output_dt_s=1.0,
      +            dr_m=BASE_DR_M,
      +            progress=True,
      +        )
      +    coarse_solution = solve_task2(
      +        data_path=data_path,
      +        t_end_s=FINAL_TIME_S,
      +        time_step_s=0.5,
      +        output_dt_s=1.0,
      +        dr_m=0.0001,
      +        progress=True,
      +    )
      +    validate_solution(coarse_solution)
      +    key_times_s, key_radius_cm, fine_temperature, fine_moisture = _key_point_values(
      +        fine_solution
      +    )
      +    _, _, coarse_temperature, coarse_moisture = _key_point_values(coarse_solution)
      +    temperature_difference = np.abs(coarse_temperature - fine_temperature)
      +    moisture_difference = np.abs(coarse_moisture - fine_moisture)
           temperature_position = np.unravel_index(
               int(np.argmax(temperature_difference)), temperature_difference.shape
           )
      @@ -565,16 +766,21 @@ def time_step_sensitivity(
           )
           return {
               "fine_solution": fine_solution,
      +        "coarse_solution": coarse_solution,
      +        "fine_dr_m": BASE_DR_M,
      +        "coarse_dr_m": 0.0001,
      +        "time_step_s": 0.5,
               "key_times_s": key_times_s,
      +        "key_radius_cm": key_radius_cm,
               "temperature_max_abs_difference_C": float(np.max(temperature_difference)),
               "temperature_difference_position": (
                   float(key_times_s[temperature_position[0]]),
      -            float(OUTPUT_RADIUS_CM[key_radius_indices[temperature_position[1]]]),
      +            float(key_radius_cm[temperature_position[1]]),
               ),
               "moisture_max_abs_difference_kgkg": float(np.max(moisture_difference)),
               "moisture_difference_position": (
                   float(key_times_s[moisture_position[0]]),
      -            float(OUTPUT_RADIUS_CM[key_radius_indices[moisture_position[1]]]),
      +            float(key_radius_cm[moisture_position[1]]),
               ),
           }
      
      @@ -594,7 +800,7 @@ def _print_key_tables(solution: dict[str, Any]) -> None:
       def main() -> None:
           parser = argparse.ArgumentParser(description="求解 A题问题二")
           parser.add_argument("--t-end", type=float, default=FINAL_TIME_S)
      -    parser.add_argument("--time-step", type=float, default=1.0)
      +    parser.add_argument("--time-step", type=float, default=0.5)
           parser.add_argument("--output-dt", type=float, default=OUTPUT_DT_S)
           parser.add_argument("--no-write", action="store_true", help="只求解和检查，不写答案文件")
           parser.add_argument("--skip-sensitivity", action="store_true")
      @@ -623,16 +829,24 @@ def main() -> None:
           if (
               not args.skip_sensitivity
               and np.isclose(args.t_end, FINAL_TIME_S)
      -        and np.isclose(args.time_step, 1.0)
      +        and np.isclose(args.time_step, 0.5)
           ):
               sensitivity = time_step_sensitivity(solution, data_path=args.data_path)
               print(
      -            "时间步敏感性（dt=1 s 对比 dt=0.5 s，表3/表4点）: "
      +            "时间步敏感性（基准 dt=0.5 s，对比 dt=1 s，dr=0.005 cm，表3/表4点）: "
                   f"max|dT|={sensitivity['temperature_max_abs_difference_C']:.6e} °C "
      27:BASE_DR_M = 0.00005
      93:    radius_m: float = RADIUS_M, dr_m: float = BASE_DR_M
      172:    normalized_residual = float(np.max(np.abs(residual)) / scale)
      173:    if not np.isfinite(normalized_residual) or normalized_residual > LINEAR_RESIDUAL_TOL:
      176:            f"normalized_inf_residual={normalized_residual:.3e}, "
      179:    return solution, normalized_residual
      198:    face_k = _harmonic_mean_positive(conductivity[:-1], conductivity[1:], "导热系数")
      199:    conductance = face_k * faces_m / dr_m
      230:    face_D = _harmonic_mean_positive(diffusivity[:-1], diffusivity[1:], "扩散系数")
      231:    conductance = face_D * faces_m / dr_m
      265:    max_linear_residual = 0.0
      288:        max_linear_residual = max(
      289:            max_linear_residual, temperature_residual, moisture_residual
      309:                max_linear_residual,
      335:    time_step_s: float = 0.5,
      337:    dr_m: float = BASE_DR_M,
      378:    linear_residuals = np.empty(n_steps, dtype=float)
      390:            linear_residuals[step - 1],
      422:        "linear_residuals": linear_residuals,
      423:        "max_linear_residual": float(np.max(linear_residuals)) if n_steps else 0.0,
      500:    linear_residuals = np.asarray(solution["linear_residuals"], dtype=float)
      504:        or linear_residuals.shape != iterations.shape
      507:    if not np.all(np.isfinite(linear_residuals)) or np.max(linear_residuals) > LINEAR_RESIDUAL_TOL:
      527:        "max_linear_residual": float(np.max(linear_residuals))
      528:        if linear_residuals.size
      664:def time_step_sensitivity(
      672:    ) and np.isclose(float(base_solution["dr_m"]), BASE_DR_M):
      680:            dr_m=BASE_DR_M,
      688:        dr_m=BASE_DR_M,
      711:        "dr_m": BASE_DR_M,
      727:def space_grid_sensitivity(
      735:    ) and np.isclose(float(base_solution["dr_m"]), BASE_DR_M):
      743:            dr_m=BASE_DR_M,
      770:        "fine_dr_m": BASE_DR_M,
      803:    parser.add_argument("--time-step", type=float, default=0.5)
      813:        f"dr={BASE_DR_M:g}m"
      834:        sensitivity = time_step_sensitivity(solution, data_path=args.data_path)
      842:        grid_sensitivity = space_grid_sensitivity(solution, data_path=args.data_path)

## Activity

    Started `/root/review_task2_optimization`

## Activity

    $ /bin/zsh -lc "/Users/jiaqiaosu/miniconda3/bin/python -c \"import pandas as pd,numpy as np; from openpyxl import load_workbook; df=pd.read_csv('solution/task2/answer/task2_all_results.csv'); assert list(df.columns)==['time_s','time_h','radius_cm','temperature_C','moisture_kgkg']; assert len(df)==226821 and df[['time_s','radius_cm']].drop_duplicates().shape[0]==226821; assert np.array_equal(df.time_s.unique(),np.arange(10801)); assert np.allclose(df.radius_cm.unique(),np.arange(21)/10); T=df.temperature_C.to_numpy().reshape(10801,21); C=df.moisture_kgkg.to_numpy().reshape(10801,21); assert np.isfinite(T).all() and np.isfinite(C).all() and C.min()>=0; assert np.max(np.abs(np.diff(T,axis=0)))<0.01 and np.max(np.abs(np.diff(C,axis=0)))<0.2; assert np.all(np.diff(T[-1])>=0) and np.all(np.diff(C[-1])<=0); wb=load_workbook('solution/task2/answer/result2.xlsx',read_only=True,data_only=True); assert wb.sheetnames==['温度','水分浓度']; arr=[]
for sn in wb.sheetnames:
 ws=wb[sn]; assert (ws.max_row,ws.max_column)==(10802,22); rows=ws.iter_rows(values_only=True); h=next(rows); assert h[0]=='时间\\\\到药材中心的距离' and np.allclose(h[1:],np.arange(21)/10); data=list(rows); assert np.array_equal(np.array([r[0] for r in data]),np.arange(10801)); arr.append(np.array([r[1:] for r in data],float))
assert np.array_equal(arr[0],T) and np.array_equal(arr[1],C); key=df[df.time_s.isin([1800,3600,5400,7200,9000,10800]) & df.radius_cm.isin([0,.5,1,1.5,2])]; assert len(key)==30; print('root输出验收: PASS'); print(f'rows={len(df)}, T={T.min():.4f}..{T.max():.4f}, C={C.min():.4f}..{C.max():.4f}'); print(f'max_1s_change_T={np.max(np.abs(np.diff(T,axis=0))):.4f}, max_1s_change_C={np.max(np.abs(np.diff(C,axis=0))):.4f}'); print(f'xlsx_csv_maxdiff={np.max(np.abs(arr[0]-T)):.1f},{np.max(np.abs(arr[1]-C)):.1f}'); print(key.to_csv(index=False))\" && shasum -a 256 problem/附件/附件3/result2.xlsx solution/task2/answer/result2.xlsx solution/task2/answer/task2_all_results.csv solution/task2/script/solve_task2.py && git diff --exit-code -- problem/附件/附件3/result2.xlsx solution/task2 && git status --short --branch"
    status: Completed · exit 0
      root输出验收: PASS
      rows=226821, T=28.0000..49.9664, C=1.0081..2.5500
      max_1s_change_T=0.0056, max_1s_change_C=0.0272
      xlsx_csv_maxdiff=0.0,0.0
      time_s,time_h,radius_cm,temperature_C,moisture_kgkg
      1800,0.5,0.0,32.19,2.5499
      1800,0.5,0.5,32.3828,2.5489
      1800,0.5,1.0,32.9666,2.5255
      1800,0.5,1.5,33.9614,2.3257
      1800,0.5,2.0,35.4135,1.6487
      3600,1.0,0.0,40.3816,2.5257
      3600,1.0,0.5,40.5536,2.4948
      3600,1.0,1.0,41.0605,2.3578
      3600,1.0,1.5,41.8783,2.023
      3600,1.0,2.0,42.9977,1.4711
      5400,1.5,0.0,45.8464,2.386
      5400,1.5,0.5,45.9345,2.3256
      5400,1.5,1.0,46.1927,2.1344
      5400,1.5,1.5,46.6048,1.802
      5400,1.5,2.0,47.1398,1.3476
      7200,2.0,0.0,48.45,2.1708
      7200,2.0,0.5,48.4878,2.1084
      7200,2.0,1.0,48.5982,1.9236
      7200,2.0,1.5,48.7733,1.6259
      7200,2.0,2.0,49.0032,1.2311
      9000,2.5,0.0,49.4668,1.9566
      9000,2.5,0.5,49.4791,1.9006
      9000,2.5,1.0,49.5135,1.736
      9000,2.5,1.5,49.5653,1.472
      9000,2.5,2.0,49.661,1.1167
      10800,3.0,0.0,49.8495,1.7662
      10800,3.0,0.5,49.8553,1.7165
      10800,3.0,1.0,49.8746,1.5702
      10800,3.0,1.5,49.9101,1.3333
      10800,3.0,2.0,49.9664,1.0081
      
      23b261b295c1b787d000eebbca6521c37075107b6fcf78724f8d395ce1798ff4  problem/附件/附件3/result2.xlsx
      0514f774b70547337ca0c9569f2cd50e09d623411f087585a0296903ed245951  solution/task2/answer/result2.xlsx
      c05f9249084b1bcef0747103354fac5ceb1b10892a91bda2738eecf7762be026  solution/task2/answer/task2_all_results.csv
      9499232bcf58a9249bff2c792af1d5f19bea17d1eccb1c60b026ddda03397120  solution/task2/script/solve_task2.py
      ## main...origin/main [ahead 4]
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store

## Activity

    agent tool: Wait · Completed

## Assistant

root 的文件级验收已通过：CSV 226821 行、XLSX 两表各 `10802×22`、两者逐点差为 0，原模板未变；温度范围 `28.0000–49.9664 °C`，水分范围 `1.0081–2.5500 kg/kg`。正在等待最后一次独立全流程复算审查。

## Activity

    agent tool: Wait · Completed

## Activity

    Interacted with `/root/review_task2_optimization`

## Activity

    Completed `/root/review_task2_optimization`

## Activity

    agent tool: Wait · Completed

## Assistant

状态：任务二已按 `handoff/task2_handoff.md` 优化完成。

已更新：

- [solve_task2.py](/Users/jiaqiaosu/Desktop/作业/2026夏季学期/2026CUMCM/2026CUMCM/solution/task2/script/solve_task2.py)
- [task2_all_results.csv](/Users/jiaqiaosu/Desktop/作业/2026夏季学期/2026CUMCM/2026CUMCM/solution/task2/answer/task2_all_results.csv)
- 已重新生成 :codex-file-citation{path="/Users/jiaqiaosu/Desktop/作业/2026夏季学期/2026CUMCM/2026CUMCM/solution/task2/answer/result2.xlsx" purpose="output"}

数值方法：

- `dr=0.00005 m`，401 个径向节点。
- 主时间步 `dt=0.5 s`，仍每 1 s 输出。
- 界面 `k、D` 改为调和平均。
- 保持后向欧拉和同状态块 Picard 迭代。
- 增加三对角线性系统归一化残差检查。
- 附件1的 `0–10800 s` 真实边界继续分段线性插值。

关键验证：

- 完整运行至 10800 s，耗时约 18.50 s。
- 无 NaN、Inf 或负含水率。
- Picard：平均 3.590648 次，最大 4 次。
- 最大线性残差：`4.52×10⁻¹⁶`。
- 温度范围：`28.0000–49.9664 °C`。
- 水分范围：`1.0081–2.5500 kg/kg`。
- 时间步敏感性：
  - 温度最大差 `7.381737×10⁻⁴ °C`
  - 水分最大差 `4.568682×10⁻⁵ kg/kg`
- 空间网格敏感性：
  - 温度最大差 `8.241737×10⁻⁶ °C`
  - 水分最大差 `7.468385×10⁻⁶ kg/kg`
- CSV 共 226821 条记录；XLSX 与 CSV 全部数值逐点一致。

表 3：温度（°C）

| 时间/h | 0 cm | 0.5 cm | 1.0 cm | 1.5 cm | 2.0 cm |
|---:|---:|---:|---:|---:|---:|
| 0.5 | 32.1900 | 32.3828 | 32.9666 | 33.9614 | 35.4135 |
| 1.0 | 40.3816 | 40.5536 | 41.0605 | 41.8783 | 42.9977 |
| 1.5 | 45.8464 | 45.9345 | 46.1927 | 46.6048 | 47.1398 |
| 2.0 | 48.4500 | 48.4878 | 48.5982 | 48.7733 | 49.0032 |
| 2.5 | 49.4668 | 49.4791 | 49.5135 | 49.5653 | 49.6610 |
| 3.0 | 49.8495 | 49.8553 | 49.8746 | 49.9101 | 49.9664 |

表 4：水分浓度（kg/kg）

| 时间/h | 0 cm | 0.5 cm | 1.0 cm | 1.5 cm | 2.0 cm |
|---:|---:|---:|---:|---:|---:|
| 0.5 | 2.5499 | 2.5489 | 2.5255 | 2.3257 | 1.6487 |
| 1.0 | 2.5257 | 2.4948 | 2.3578 | 2.0230 | 1.4711 |
| 1.5 | 2.3860 | 2.3256 | 2.1344 | 1.8020 | 1.3476 |
| 2.0 | 2.1708 | 2.1084 | 1.9236 | 1.6259 | 1.2311 |
| 2.5 | 1.9566 | 1.9006 | 1.7360 | 1.4720 | 1.1167 |
| 3.0 | 1.7662 | 1.7165 | 1.5702 | 1.3333 | 1.0081 |

Git：

- `9499d02c13dbdcbd83a0f27f62664765804cecdf` — `按交接规范优化问题二数值求解`

该提交仅包含三个 `solution/task2/` 目标文件，未推送。

## Activity

    $ /bin/zsh -lc 'git status'
    status: Completed · exit 0
      On branch main
      Your branch is ahead of 'origin/main' by 4 commits.
        (use "git push" to publish your local commits)
      
      Untracked files:
        (use "git add <file>..." to include in what will be committed)
      	.DS_Store
      	solution/.DS_Store
      	solution/task2/.DS_Store
      
      nothing added to commit but untracked files present (use "git add" to track)
