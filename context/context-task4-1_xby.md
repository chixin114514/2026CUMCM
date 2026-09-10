# Codex conversation

## User

你现在位于项目仓库根目录 `2026CUMCM`。当前唯一目标是完成 2026 年高教社杯数学建模 A 题“药材的烘干问题”的【问题四】真实数值求解，并产出最终可提交结果。

当前项目结构大致如下：

2026CUMCM
├── context
│   └── context-task1-1_xby.md
├── handoff
│   ├── task1_gjs_handoff.md
│   └── task1_xby_handoff.md
├── problem
│   ├── A题.md
│   ├── A题.pdf
│   └── 附件
│       ├── 附件1.xlsx
│       ├── 附件2.xlsx
│       └── 附件3
│           ├── result1.xlsx
│           ├── result2.xlsx
│           ├── result3.xlsx
│           └── result4.xlsx
└── solution
    └── task1
        ├── answer
        │   ├── task1_key_results.csv
        │   └── task1_result.csv
        └── script
            └── solve_task1.py

如果仓库中实际上已经存在 task2、task3 的 solution、context 或 handoff 文件，也必须主动检查并优先复用其中已经验证过的模型、边界条件和数值实现。不要因为上面的目录树没有列出就假设它们不存在。

====================
一、你的角色
====================

你是 `5.6-sol medium`，是本任务的根模型。

你的职责仅包括：
1. 理解问题四；
2. 阅读题目和已有任务成果；
3. 决定数学建模和数值求解方案；
4. 将具体实现任务拆给 `luna-worker`；
5. 审查 luna-worker 的代码、计算结果和文件；
6. 判断结果是否可信；
7. 向我汇报最终结果。

你不要亲自承担具体代码实现。

凡是涉及以下操作，都应主动派出 `luna-worker`：
- 编写或修改 Python 代码；
- 数据读取和处理；
- 数值求解；
- 调试；
- 创建或修改 xlsx；
- 创建 csv；
- 执行脚本；
- 数值验证；
- Git 文件修改。

根模型负责决策和验收，luna-worker 负责落实。

不要把 luna-worker 的结果直接视为正确。每次 worker 完成后，你都必须检查其模型、结果和数值证据，再决定是否进入下一阶段。

====================
二、任务目标
====================

只解决 A 题问题四。

首先完整阅读：

`problem/A题.md`

重点理解：
- 问题四；
- 问题三的结束条件；
- 附录 4；
- result4.xlsx 的格式要求。

问题四是在前面整个烘干过程模型的基础上进一步考虑药材因失水发生的尺寸变化。

必须读取：

`problem/附件/附件2.xlsx`

其中给出了烘干过程中不同时间对应的药材半径。

附件数据本身是正确的。

禁止浪费时间检查附件是否损坏、是否可信、有没有版权问题、题目数据是否合理等与求解无关的事情。

只进行程序正常读取所必需的数据解析。

如果存在已经完成的 task2/task3 求解程序，应把问题四视为对问题三模型的扩展，优先复用已有模型。

问题四原则上只引入题目要求的变化：
1. 半径 R 随时间变化；
2. 热物性和水分扩散经验公式改用附录 4；
3. 输出格式改为问题四要求。

除非题目明确要求，否则不要自行改变前面任务已经确定的烘房环境条件、初始条件、对流换热条件、对流传质条件等。

====================
三、问题四必须建立的数学模型
====================

问题四的关键是【移动边界】。

药材初始近似为半径约 2 cm 的圆柱体，附件 2 给出了：

R = R(t)

因此空间计算域为：

0 ≤ r ≤ R(t)

不能简单地在原固定半径网格上把 R=2 cm 换成一个随时间变化的数字，然后继续使用原固定区域方程。

必须真正处理移动边界。

优先采用可解释、可复现的固定域坐标变换，例如：

ξ = r / R(t)，0 ≤ ξ ≤ 1

把随时间收缩的物理区域映射到固定计算区域。

需要由根模型明确推导或检查坐标变换后热传导和水分扩散方程中由于 R(t) 变化产生的项，包括空间导数缩放以及必要的移动坐标项。

不要用无法说明内部机制的黑箱方案替代这个建模步骤。

附件 2 的离散半径数据需要构造 R(t)。

优先使用简单、透明的插值方法，例如分段线性插值。

如果没有充分理由，不要引入高阶样条、复杂拟合模型或额外经验参数。

如果需要 dR/dt，应使用与 R(t) 插值相匹配、可解释的方式求取。

药材仍按一维径向长圆柱模型处理。

附件 2 只给出半径变化，因此不要自行引入轴向收缩模型。

====================
四、热湿耦合关系
====================

问题四使用附录 4 给出的经验公式：

ρ = 760 + 90C

cp = 1850 + 2150 * C/(C+1)

k = 0.12 + 0.20 * C/(C+1)

D = 4.2×10^-4 * exp(-0.30/C) * exp(-3850/T)

其中：
- ρ：kg/m³
- cp：J/(kg·K)
- k：W/(m·K)
- D：m²/s
- C：kg/kg
- T：K

特别注意：

D 中的 T 必须使用 Kelvin。

虽然问题四最终只要求输出水分浓度，但 D 与 T 有关，同时附录 4 给出了 ρ、cp、k，因此必须继续求解温度场，并让温度场参与水分扩散系数计算。

禁止把温度简单设成烘房温度来规避热传导方程，除非前面经过严格验证已经证明可以如此简化。

如果 task2/task3 已存在经过验证的热湿耦合模型，应以其方程、边界条件和环境条件为基线，仅做问题四要求的修改。

====================
五、结束条件
====================

问题三和问题四的烘干要求保持：

药材各处水分浓度均低于 0.15 kg/kg。

因此定义：

C_max(t) = max_{0≤r≤R(t)} C(r,t)

烘干结束时间为满足：

C_max(t) < 0.15

的最早时刻。

不能只检查药材表面。

不能只检查药材中心。

不能使用平均水分浓度作为结束条件。

需要明确给出结束时刻附近的数值证据，例如：
- 结束时刻；
- 结束时 C_max；
- C_max 出现的位置；
- 结束前一个计算时刻的 C_max。

最终烘干时长应尽可能通过事件搜索、局部加密或其他简单可解释方式确定，而不能机械地把“第一个 60 s 输出点满足条件”直接当成真实结束时间。

保存结果仍按题目要求的 60 s 时间间隔进行。

====================
六、数值求解原则
====================

目标是得到可信的竞赛数值结果，不进行过度工程化。

优先：
- 复用 task2/task3 已验证数值求解器；
- 使用成熟、透明的有限差分或有限体积离散；
- 使用固定 ξ 网格处理移动边界；
- 使用足以保证结果稳定的时间步和空间步；
- 进行必要的网格/时间步敏感性检查。

不要：
- 建大型框架；
- 为只有一个脚本的任务设计复杂类层次；
- 加数据库；
- 加 Web 服务；
- 写大量与最终结果无关的测试；
- 为几乎不可能发生的输入错误设计复杂异常体系；
- 对附件进行所谓“鲁棒性清洗”；
- 讨论版权、安全、部署、API 等无关问题；
- 为追求形式上的工程质量牺牲求解进度。

原则是：

先得到数学正确、数值可靠、可复现的最终答案。

====================
七、目录与文件
====================

创建：

solution/task4/
├── script/
│   └── solve_task4.py
└── answer/
    ├── result4.xlsx
    ├── task4_paper_table.xlsx
    └── task4_all_answers.csv

不要覆盖：

`problem/附件/附件3/result4.xlsx`

它是原始模板。

应该复制模板或按照模板结构生成：

`solution/task4/answer/result4.xlsx`

====================
八、result4.xlsx
====================

严格按照 `A题.md` 和原始模板：

`problem/附件/附件3/result4.xlsx`

生成最终：

`solution/task4/answer/result4.xlsx`

题目要求：
- 保存水分浓度，单位 kg/kg；
- 时间每隔 60 s；
- 到药材中心距离每隔 0.1 cm；
- A 列为时间，单位 s；
- 第 1 行为空间位置；
- 所有最终结果保留四位小数。

必须保持官方模板要求的工作表名称、表头结构、行列结构和顺序。

不要擅自重新设计 result4.xlsx。

对于收缩以后已经位于药材表面之外的固定绝对坐标，不允许凭空外推水分浓度。

应首先检查官方 result4.xlsx 模板如何定义这些位置，然后按模板语义处理。

如果确实出现模板无法唯一决定的情况，并且不同处理会改变提交结果，再向我询问。除此之外不要因为轻微歧义停下来。

====================
九、论文版 task4_paper_table.xlsx
====================

另外生成：

`solution/task4/answer/task4_paper_table.xlsx`

它对应 A题表 6，可直接供论文整理使用。

时间行：

6 h
12 h
18 h
……
烘干结束时间

一直列到实际烘干结束。

空间列按照题目要求：

0 cm
0.5 cm
1.0 cm
1.5 cm
……
药材表面

具体列数根据实际半径和题目表 6 的含义合理生成。

“药材表面”必须使用该时刻真实的：

r = R(t)

对应的水分浓度。

不能继续把 r=2 cm 当成药材表面。

所有数值保留四位小数。

同时在表格中明确给出最终烘干时长。

====================
十、CSV 总结果
====================

生成一个：

`solution/task4/answer/task4_all_answers.csv`

该 CSV 必须能够包含问题四所有数值答案，不能只有表 6 的少量数据。

为了适应 R(t) 变化，推荐采用长表形式，例如字段：

record_type
time_s
time_h
radius_cm
r_cm
is_surface
temperature_C
moisture_kgkg

其中至少完整包含：
- 每隔 60 s；
- 每隔 0.1 cm；
- 每个有效药材内部位置的水分浓度；
- 对应时刻实际半径 R(t)；
- 必要的温度值；
- 药材表面点；
- 最终烘干时长。

可以增加少量真正有用的字段，但不要创建大量无意义元数据。

CSV 应保证后续能够独立重建 result4.xlsx 和表 6。

====================
十一、必要验证
====================

完成求解后必须检查：

1. 初始半径、附件 2 各已知时间点半径与程序读取结果一致。

2. R(t) 的变化与附件 2 一致，不能出现由于插值或单位错误导致的异常半径。

3. 中心 r=0 满足圆柱径向对称边界条件。

4. r=R(t) 使用真实移动表面边界条件。

5. 温度单位进入指数公式前已转换成 K。

6. C 不应出现明显非物理负值、NaN 或 Inf。

7. 输出时间和空间采样严格符合题目要求。

8. 烘干结束条件确实是整个当前药材区域：
   max C < 0.15 kg/kg。

9. 检查结束时刻前后 C_max 的跨阈值情况。

10. 做一次成本较低的数值敏感性检查，例如将内部时间步或空间网格加密一次，观察最终烘干时长和关键水分浓度是否基本稳定。

敏感性检查只用于确认答案稳定，不需要发展成完整数值分析论文。

如果 task3 已有结果，还应进行一个合理性对比：

问题四相对于问题三发生了：
- 参数经验公式变化；
- 药材半径收缩；
- 移动边界。

因此结果发生差异是正常的，但必须能够解释差异来自哪里。

不要事先强行规定问题四一定比问题三快多少。

====================
十二、Git 版本管理
====================

版本管理是强制要求。

开始前先执行：

git status

不得覆盖、删除或提交与本任务无关的用户修改。

每完成一个可以独立运行、独立验收的版本，都必须 commit。

所有 commit message 必须使用中文。

禁止使用英文 commit message。

例如可以采用：

`建立问题四移动边界求解框架`

`实现药材收缩条件下的热湿耦合求解`

`生成问题四完整结果文件`

`修正问题四结束时间并完成数值验证`

这只是示例，实际 commit 内容必须和修改内容一致。

每次 commit 前：
- 检查 git diff；
- 只提交本阶段相关文件；
- 不提交 `.DS_Store` 等垃圾文件；
- 确认脚本至少可以运行到当前版本预期状态。

最终完成时工作树中不应残留本任务遗漏的应提交修改。

====================
十三、执行顺序
====================

你作为根模型按以下流程推进：

第一阶段：
阅读 `A题.md`、附件 2，以及已有 task2/task3 代码和上下文，确定问题四相对于问题三到底修改哪些方程和参数。

第二阶段：
由你给出清晰的数学模型方案，重点确认移动边界处理方式，然后派 luna-worker 实现。

第三阶段：
运行数值求解，先获得烘干结束时间和关键水分场结果。

第四阶段：
审查结果是否满足物理规律和数值稳定性。如果发现问题，由 luna-worker 定向修复，不要无目的重构。

第五阶段：
生成：
- result4.xlsx
- task4_paper_table.xlsx
- task4_all_answers.csv

第六阶段：
重新读取最终文件进行验收，确认行数、列数、采样间隔、单位、四位小数、结束时间和阈值条件全部正确。

第七阶段：
完成最终 Git commit。

====================
十四、最终向我汇报
====================

全部完成后，只给我高价值结果。

至少报告：

1. 最终烘干时长，单位 h；
2. 烘干结束时最大水分浓度及其空间位置；
3. 问题四采用的移动边界处理方法；
4. 相比问题三模型修改了哪些核心部分；
5. 数值敏感性检查结果；
6. 三个最终输出文件路径；
7. 最终 Git commit hash；
8. 是否存在仍未解决的问题。

如果没有剩余问题，明确写：

`剩余问题：无`

不要给我长篇流水账。

====================
十五、核心执行原则
====================

以最终答案为导向。

优先解决会改变最终数值答案的问题。

对建模决策必须保持可解释、可复现。

遇到真正会导致两种不同数学答案的关键歧义时再询问我。

普通代码细节、文件路径、插值实现、数值计算方式等问题由你和 luna-worker 自主解决。

严禁过度工程化。

## Assistant

状态：先核对仓库现状、既有 task2/task3 成果和问题四原始格式，再确定移动边界方程。实现、运行、生成文件和 Git 提交将全部交由 `luna-worker`；我只负责模型决策与逐阶段验收。

我会使用 `writing-plans` 约束分阶段实施，并在最终交付前使用 `verification-before-completion` 做证据验收。

## Activity

    $ /bin/zsh -lc "git status --short && rg -n \"2026CUMCM|药材|task4|问题四|task3\" /Users/jiaqiaosu/.codex/memories/MEMORY.md | head -80 && printf '\\n--- writing-plans ---\\n' && sed -n '1,240p' /Users/jiaqiaosu/.agents/skills/writing-plans/SKILL.md && printf '\\n--- verification ---\\n' && sed -n '1,240p' /Users/jiaqiaosu/.agents/skills/verification-before-completion/SKILL.md"
    status: Completed · exit 0
      A  context/context-task2-1_xby.md
      A  handoff/task2_gjs_handoff.md
      ?? .DS_Store
      ?? handoff/task2_handoff.md
      ?? handoff/task3_gjs_handoff.md
      ?? handoff/task3_xby_handoff.md
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/
      51:applies_to: cwd=machine-level Codex session state, initiated from `/Users/jiaqiaosu/Desktop/作业/2026夏季学期/jiqiren/2026Summer_IntegratedRobotProgram_Group-Team_fullcans/task3`; reuse_rule=re-check the target thread, JSONL path, lock holder, and installed CLI/app state before reuse; never assume an empty lock file or a prior `turn_aborted` is safe to delete
      57:- rollout_summaries/2026-09-09T08-32-07-cqdI-codex_active_writer_resume_lock_fix.md (cwd=/Users/jiaqiaosu/Desktop/作业/2026夏季学期/jiqiren/2026Summer_IntegratedRobotProgram_Group-Team_fullcans/task3, rollout_path=/Users/jiaqiaosu/.codex/sessions/2026/09/09/rollout-2026-09-09T16-32-07-01a0854b-ba28-7213-98f1-5eb49b2fb85a.jsonl, updated_at=2026-09-09T08:39:46+00:00, thread_id=01a0854b-ba28-7213-98f1-5eb49b2fb85a, target session resumed; `codex doctor` was user-stopped)
      149:applies_to: cwd=/Users/jiaqiaosu/Desktop/作业/2026夏季学期/jiqiren/2026Summer_IntegratedRobotProgram_Group-Team_fullcans/task3 with Jetson workspace `/home/nvidia/Desktop/2026Summer_IntegratedRobotProgram_Group-Team_fullcans/task3/ros2_ws`; reuse_rule=re-check Jetson connectivity, installed colcon extensions, deployed workspace, and live Gazebo state before reuse because package/runtime state is host- and time-specific
      155:- rollout_summaries/2026-09-08T06-09-59-3yPF-task3_independent_phase1_gazebo_scene.md (cwd=/Users/jiaqiaosu/Desktop/作业/2026夏季学期/jiqiren/2026Summer_IntegratedRobotProgram_Group-Team_fullcans/task3, rollout_path=/Users/jiaqiaosu/.codex/sessions/2026/09/08/rollout-2026-09-08T14-09-59-01a07fa3-3bcb-7c41-a59b-85cada794373.jsonl, updated_at=2026-09-08T07:43:21+00:00, thread_id=01a07fa3-3bcb-7c41-a59b-85cada794373, Jetson environment and independence constraints verified)
      165:- rollout_summaries/2026-09-08T06-09-59-3yPF-task3_independent_phase1_gazebo_scene.md (cwd=/Users/jiaqiaosu/Desktop/作业/2026夏季学期/jiqiren/2026Summer_IntegratedRobotProgram_Group-Team_fullcans/task3, rollout_path=/Users/jiaqiaosu/.codex/sessions/2026/09/08/rollout-2026-09-08T14-09-59-01a07fa3-3bcb-7c41-a59b-85cada794373.jsonl, updated_at=2026-09-08T07:43:21+00:00, thread_id=01a07fa3-3bcb-7c41-a59b-85cada794373, 18 static tests and Jetson build passed; package discovery/live acceptance remain blocked)
      169:- task3_sim, mycobot_description, mecharm_270_gazebo.urdf, task3_world.sdf, scene.yaml, task3_scene.launch.py, /task3/camera/image_raw, ros2 pkg prefix, Package not found, colcon-ros, AMENT_PREFIX_PATH, IGN_PARTITION
      175:- when the user said “taskpoints，taskmanager，resultmonitor这三个文件和task3无关系，不建议复用” -> do not reuse Task2 point configuration, task manager, or result monitor. [Task 1]
      181:- Task3 owns `ros2_ws/src/mycobot_description` and `ros2_ws/src/task3_sim`; key files are `worlds/task3_world.sdf`, `config/scene.yaml`, `launch/task3_scene.launch.py`, and `test/`. The copied `mecharm_270_gazebo.urdf`, seven DAE meshes, and vendor LICENSE are 9/9 byte-identical to `tak2`; historical `/task2/...` Gazebo topic strings inside the immutable URDF do not mean Task3 depends on Task2. [Task 2]
      183:- The camera is `/task3/camera/image_raw`, 640x480, 30 Hz, `R8G8B8`. Launch bridges `/clock` and image, starts `robot_state_publisher`, runs `ign gazebo -r`, then spawns `mecharm_270` through `/world/task3_world/create`. Recorded local proof: `Ran 18 tests ... OK`, XML/SDF `4/4`, immutable assets `9/9`, runtime isolation scan clean, Python compilation and `git diff --check`. [Task 2]
      184:- Jetson `colcon build --symlink-install --packages-select mycobot_description task3_sim` completed both packages, but the host lacks `python3-colcon-ros`. After authorization, install `python3-colcon-ros` (or `python3-colcon-common-extensions`), rebuild/source, then re-run `ros2 pkg prefix` before attempting `ros2 launch task3_sim task3_scene.launch.py`. [Task 1][Task 2]
      189:- symptom: rsync fails because the Task3 remote destination is missing. Cause: the multi-level parent directory does not exist. Fix: first run SSH `mkdir -p .../task3/ros2_ws`, then sync. [Task 1]
      190:- symptom: a worker creates `task3.launch.py` or imports Task2 runtime. Cause: the approved Task3 naming/isolation contract was not checked. Fix: standardize against the plan before deployment and scan Task3-owned runtime files for Task2 references. [Task 2]
      197:applies_to: cwd=machine-level `/Users/jiaqiaosu/.codex/agents` configuration, initiated from `/Users/jiaqiaosu/Desktop/作业/2026夏季学期/jiqiren/2026Summer_IntegratedRobotProgram_Group-Team_fullcans/task3`; reuse_rule=re-check installed Codex CLI schema/version before editing because accepted fields can change
      203:- rollout_summaries/2026-09-08T05-33-18-oxHx-create_validate_luna_worker_agent_config.md (cwd=/Users/jiaqiaosu/Desktop/作业/2026夏季学期/jiqiren/2026Summer_IntegratedRobotProgram_Group-Team_fullcans/task3, rollout_path=/Users/jiaqiaosu/.codex/sessions/2026/09/08/rollout-2026-09-08T13-33-18-01a07f81-a806-7361-b941-1703c7653f6f.jsonl, updated_at=2026-09-08T06:08:29+00:00, thread_id=01a07f81-a806-7361-b941-1703c7653f6f, TOML parser and strict doctor validation passed)
      
      --- writing-plans ---
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
      
      --- verification ---
      ---
      name: verification-before-completion
      description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
      ---
      
      # Verification Before Completion
      
      ## Overview
      
      Claiming work is complete without verification is dishonesty, not efficiency.
      
      **Core principle:** Evidence before claims, always.
      
      **Violating the letter of this rule is violating the spirit of this rule.**
      
      ## The Iron Law
      
      ```
      NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
      ```
      
      If you haven't run the verification command in this message, you cannot claim it passes.
      
      ## The Gate Function
      
      ```
      BEFORE claiming any status or expressing satisfaction:
      
      1. IDENTIFY: What command proves this claim?
      2. RUN: Execute the FULL command (fresh, complete)
      3. READ: Full output, check exit code, count failures
      4. VERIFY: Does output confirm the claim?
         - If NO: State actual status with evidence
         - If YES: State claim WITH evidence
      5. ONLY THEN: Make the claim
      
      Skip any step = lying, not verifying
      ```
      
      ## Common Failures
      
      | Claim | Requires | Not Sufficient |
      |-------|----------|----------------|
      | Tests pass | Test command output: 0 failures | Previous run, "should pass" |
      | Linter clean | Linter output: 0 errors | Partial check, extrapolation |
      | Build succeeds | Build command: exit 0 | Linter passing, logs look good |
      | Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
      | Regression test works | Red-green cycle verified | Test passes once |
      | Agent completed | VCS diff shows changes | Agent reports "success" |
      | Requirements met | Line-by-line checklist | Tests passing |
      
      ## Red Flags - STOP
      
      - Using "should", "probably", "seems to"
      - Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
      - About to commit/push/PR without verification
      - Trusting agent success reports
      - Relying on partial verification
      - Thinking "just this once"
      - Tired and wanting work over
      - **ANY wording implying success without having run verification**
      
      ## Rationalization Prevention
      
      | Excuse | Reality |
      |--------|---------|
      | "Should work now" | RUN the verification |
      | "I'm confident" | Confidence ≠ evidence |
      | "Just this once" | No exceptions |
      | "Linter passed" | Linter ≠ compiler |
      | "Agent said success" | Verify independently |
      | "I'm tired" | Exhaustion ≠ excuse |
      | "Partial check is enough" | Partial proves nothing |
      | "Different words so rule doesn't apply" | Spirit over letter |
      
      ## Key Patterns
      
      **Tests:**
      ```
      ✅ [Run test command] [See: 34/34 pass] "All tests pass"
      ❌ "Should pass now" / "Looks correct"
      ```
      
      **Regression tests (TDD Red-Green):**
      ```
      ✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
      ❌ "I've written a regression test" (without red-green verification)
      ```
      
      **Build:**
      ```
      ✅ [Run build] [See: exit 0] "Build passes"
      ❌ "Linter passed" (linter doesn't check compilation)
      ```
      
      **Requirements:**
      ```
      ✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
      ❌ "Tests pass, phase complete"
      ```
      
      **Agent delegation:**
      ```
      ✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
      ❌ Trust agent report
      ```
      
      ## Why This Matters
      
      From 24 failure memories:
      - your human partner said "I don't believe you" - trust broken
      - Undefined functions shipped - would crash
      - Missing requirements shipped - incomplete features
      - Time wasted on false completion → redirect → rework
      - Violates: "Honesty is a core value. If you lie, you'll be replaced."
      
      ## When To Apply
      
      **ALWAYS before:**
      - ANY variation of success/completion claims
      - ANY expression of satisfaction
      - ANY positive statement about work state
      - Committing, PR creation, task completion
      - Moving to next task
      - Delegating to agents
      
      **Rule applies to:**
      - Exact phrases
      - Paraphrases and synonyms
      - Implications of success
      - ANY communication suggesting completion/correctness
      
      ## The Bottom Line
      
      **No shortcuts for verification.**
      
      Run the command. Read the output. THEN claim the result.
      
      This is non-negotiable.

## Activity

    Started `/root/task4_phase1`

## Activity

    $ /bin/zsh -lc "rg --files -g '"'!*.pyc'"' -g '"'!__pycache__'"' | sort && printf '\\n--- A题 relevant headings ---\\n' && rg -n \"问题三|问题四|附录 4|附录4|表 6|表6|result4|0.15|60 s|60s\" problem/A题.md && printf '\\n--- existing task2/task3 text files ---\\n' && for f in context/*task[23]* handoff/*task[23]* solution/task2/script/*.py solution/task3/script/*.py; do test -f \""'$f" && printf '"'\\n===== %s =====\\n' \""'$f" && sed -n '"'1,260p' \""'$f"; done'
    status: Completed · exit 0
      context/context-task1-1_xby.md
      context/context-task2-1_xby.md
      handoff/task1_gjs_handoff.md
      handoff/task1_handoff.md
      handoff/task1_xby_handoff.md
      handoff/task2_gjs_handoff.md
      handoff/task2_handoff.md
      handoff/task2_xby_handoff.md
      handoff/task3_gjs_handoff.md
      handoff/task3_xby_handoff.md
      problem/A题.md
      problem/A题.pdf
      problem/附件/附件1.xlsx
      problem/附件/附件2.xlsx
      problem/附件/附件3/result1.xlsx
      problem/附件/附件3/result2.xlsx
      problem/附件/附件3/result3.xlsx
      problem/附件/附件3/result4.xlsx
      solution/task1/answer/task1_key_results.csv
      solution/task1/answer/task1_result.csv
      solution/task1/script/solve_task1.py
      solution/task2/answer/result2.xlsx
      solution/task2/answer/task2_all_results.csv
      solution/task2/script/solve_task2.py
      solution/task3/answer/result3.xlsx
      solution/task3/answer/task3_all_results.csv
      solution/task3/script/solve_task3.py
      
      --- A题 relevant headings ---
      15:请建立预热平衡阶段药材温度和水分浓度变化规律的数学模型（相关参数见附录 2），在论文中按表 1 和表 2 的格式分别给出 100、300、600、900、1200、1500、1800 s，到药材中心距离 0、0.5、1、1.5、2 cm 处的结果，并将 1800 s 内每隔 1 s、到药材中心距离每隔 0.1 cm 的完整结果保存到文件 `result1.xlsx` 中（模板文件见附件 3）。所有结果保留四位小数（下同）。
      77:按照烘干要求，药材各处的水分浓度应低于 0.15 kg/kg，请确定药材烘干所需要的时间（单位：h）。
      79:在论文中按表 5 的格式给出每隔 6 h、到药材中心距离每隔 0.5 cm 的水分浓度，并将药材内部水分浓度每隔 60 s、到药材中心距离每隔 0.1 cm 的完整结果保存到文件 `result3.xlsx` 中（模板文件见附件 3）。
      95:在实际烘干过程中，药材会因水分流失发生尺寸变化。请根据附件 2，确定药材的烘干时长（相关经验公式见附录 4）。
      97:在论文中按表 6 的格式给出每隔 6 h、到药材中心距离每隔 0.5 cm 的水分浓度，并将药材内部水分浓度每隔 60 s 时间、0.1 cm 距离的完整结果保存到文件 `result4.xlsx` 中（模板文件见附件 3）。
      99:### 表 6 药材烘干过程的水分浓度
      117:附件 3 是结果文件夹，包括 4 个文件（`result1.xlsx`-`result4.xlsx`）。
      131:## result4.xlsx 问题 4 的结果模板文件
      179:# 附录 4 问题 4 的相关经验公式
      
      --- existing task2/task3 text files ---
      
      ===== context/context-task2-1_xby.md =====
      # Codex conversation
      
      ## User
      
      你现在负责 2026CUMCM 项目的 A 题问题二真实求解。
      
      你的身份是根模型，模型为 5.6-sol medium。
      
      你的核心职责只有：
      1. 准确理解用户意图和题目要求；
      2. 阅读已有上下文、问题一 handoff 和问题一代码；
      3. 制定尽可能短的执行路径；
      4. 主动派出 luna-worker 完成代码编写、文件修改、程序运行、数值计算、结果文件生成等执行工作；
      5. 对 luna-worker 的结果进行检查和验收；
      6. 最终向用户汇报结果、文件位置、数值验证情况和 commit。
      
      你作为 root 不要亲自承担大段代码实现工作。凡是代码编写、修改脚本、运行求解器、生成 xlsx/csv、修复运行错误等执行任务，应主动委派给 luna-worker。
      
      ==================================================
      一、项目结构
      ==================================================
      
      项目当前结构：
      
      2026CUMCM
      ├── context
      │   └── context-task1-1_xby.md
      ├── handoff
      │   ├── task1_gjs_handoff.md
      │   └── task1_xby_handoff.md
      ├── problem
      │   ├── A题.md
      │   ├── A题.pdf
      │   └── 附件
      │       ├── 附件1.xlsx
      │       ├── 附件2.xlsx
      │       └── 附件3
      │           ├── result1.xlsx
      │           ├── result2.xlsx
      │           ├── result3.xlsx
      │           └── result4.xlsx
      └── solution
          └── task1
              ├── answer
              │   ├── task1_key_results.csv
              │   └── task1_result.csv
              └── script
                  └── solve_task1.py
      
      问题二必须建立：
      
      solution/task2/
      ├── answer/
      │   ├── result2.xlsx
      │   └── task2_all_results.csv
      └── script/
          └── solve_task2.py
      
      不要修改 problem/ 下的原始题目和附件。
      
      尤其不要直接覆盖：
      
      problem/附件/附件3/result2.xlsx
      
      应复制其模板结构并生成：
      
      solution/task2/answer/result2.xlsx
      
      ==================================================
      二、第一步必须阅读已有工作，不允许重新发明问题一
      ==================================================
      
      开始前先阅读：
      
      problem/A题.md
      context/context-task1-1_xby.md
      handoff/task1_xby_handoff.md
      handoff/task1_gjs_handoff.md
      solution/task1/script/solve_task1.py
      
      其中：
      
      task1_xby_handoff.md 和 context-task1-1_xby.md 是理解问题一最终模型和数值实现的重要依据。
      
      你的目标不是重新讨论问题一，也不是重新设计整套 PDE。
      
      问题二应最大程度复用问题一已经验证过的：
      
      - 圆柱径向一维建模假设；
      - 温度 PDE；
      - 水分 PDE；
      - 中心对称条件；
      - 表面对流换热条件；
      - 表面对流传质条件；
      - 空间离散方法；
      - 时间积分框架；
      - 附件 1 的读取和插值方法；
      - 已验证的数值处理方式。
      
      只有问题二明确要求变化的部分才修改。
      
      不要因为存在另一种可能的模型就推翻问题一。
      
      ==================================================
      三、问题二的核心数学任务
      ==================================================
      
      问题二的本质是：
      
      问题一中材料物性相对固定；
      
      问题二中材料物性随着当前温度和含水率动态变化。
      
      在每个时刻、每个空间节点，都有：
      
      T = 当前药材温度
      C = 当前药材干基含水率
      
      然后使用附录 3：
      
      ρ = 650 + 128 C
      
      cp = 1450 + 2736 * C / (C + 1)
      
      k = 0.21 + 0.38 * C / (C + 1)
      
      D = 2.4e-3 * exp(-0.45 / C) * exp(-3850 / T)
      
      注意：
      
      - ρ 单位 kg/m^3
      - cp 单位 J/(kg·K)
      - k 单位 W/(m·K)
      - D 单位 m^2/s
      - C 单位 kg/kg
      - D 公式中的 T 必须使用 Kelvin
      - 温度结果输出仍然使用 °C
      
      不要把这些公式只在初始时刻算一次。
      
      它们必须随着 T(r,t)、C(r,t) 的变化不断更新。
      
      问题二的基本迭代逻辑是：
      
      (T^n, C^n)
          ↓
      计算当前 ρ^n, cp^n, k^n, D^n
          ↓
      求解当前时间步的传热、传质 PDE
          ↓
      得到新的 T^(n+1), C^(n+1)
          ↓
      重新计算物性
          ↓
      继续下一时间步
      
      ==================================================
      四、非线性求解要求
      ==================================================
      
      优先采用清晰、容易解释、避免黑箱的方法。
      
      推荐在每个时间步内部使用 Picard 迭代，使：
      
      T、C
      
      与：
      
      ρ(C)、cp(C)、k(C)、D(C,T)
      
      在当前时间步内达到自洽。
      
      概念流程：
      
      已知 T^n、C^n
      
      第一次：
      
      用 T^n、C^n 计算
      ρ^(0)、cp^(0)、k^(0)、D^(0)
      
      求解得到临时：
      T^(1)、C^(1)
      
      然后：
      
      用 T^(1)、C^(1) 更新
      ρ^(1)、cp^(1)、k^(1)、D^(1)
      
      重新求当前时间步。
      
      直到当前时间步内：
      
      max |T^(m+1)-T^(m)|
      
      和
      
      max |C^(m+1)-C^(m)|
      
      足够小。
      
      Picard 收敛阈值选择一个正常、合理、能够稳定求解的数量级即可。
      
      不要为了追求理论形式无限降低阈值。
      
      如果问题一已经采用一个可靠的隐式时间积分方法，优先在这个基础上增加 Picard 外迭代，不要重新换一套求解框架。
      
      如果实践证明单步冻结系数已经与 Picard 结果几乎一致，可以保留 Picard 作为最终方法或给出数值比较，但不要为此建立复杂架构。
      
      ==================================================
      五、时间和空间范围
      ==================================================
      
      问题二求解前 3 h：
      
      0 <= t <= 10800 s
      
      药材半径：
      
      0 <= r <= 2 cm
      
      问题二暂时不考虑尺寸收缩。
      
      尺寸变化属于问题四。
      
      结果文件要求：
      
      时间输出间隔：
      1 s
      
      空间输出位置：
      
      0.0 cm
      0.1 cm
      0.2 cm
      ...
      2.0 cm
      
      即共 21 个径向输出位置。
      
      内部数值网格可以继承 task1 的设置。
      
      如果 task1 使用更细空间网格，则继续使用更细的内部网格，最后插值得到每隔 0.1 cm 的结果。
      
      不要为了刚好匹配输出间隔而降低内部求解精度。
      
      ==================================================
      六、初始状态和烘房条件
      ==================================================
      
      问题二从整个烘干过程 t=0 开始计算。
      
      沿用题目给出的初始药材状态：
      
      T(r,0) = 28 °C
      
      C(r,0) = 2.55 kg/kg
      
      初始时在整个径向上均匀。
      
      
      ===== handoff/task2_gjs_handoff.md =====
      # A题第二问：整个烘干过程的温度—水分双向耦合模型与计算结果
      
      ## 1. 建模思路
      
      第二问沿用第一问的基本框架：把药材近似为半径 \(R=2\ \mathrm{cm}\)、长度 \(L=25\ \mathrm{cm}\) 的均匀圆柱体，只研究从中心到表面的径向传热和水分迁移。
      
      第二问与第一问的关键区别在于附录3：
      
      - 密度 \(\rho\)、比热容 \(c_p\) 和导热系数 \(k\) 都随水分浓度 \(C\) 改变；
      - 水分扩散系数 \(D\) 同时取决于温度 \(T\) 和水分浓度 \(C\)；
      - 因此 \(C\) 会影响温度场，温度场又会反过来影响水分场，两个方程必须迭代求解。
      
      附件1给出了 \(0\sim14400\ \mathrm s\) 的烘房数据，而第二问只计算前三小时，即 \(0\sim10800\ \mathrm s\)，所以计算范围完全处于附件数据内部，不需要外推。
      
      附件1中的烘房温度由 \(28^\circ\mathrm C\) 逐渐升高，并在约 \(2.5\sim3\ \mathrm h\) 后稳定在 \(50^\circ\mathrm C\) 左右，数据本身已经描述了预热向恒温干燥的过渡。附录3又要求两个阶段统一使用同一组经验公式，所以不需要人为切换控制方程。
      
      ## 2. 模型假设
      
      1. 药材为均匀、各向同性的圆柱体；
      2. 第二问不考虑药材收缩，半径始终取 \(R=0.02\ \mathrm m\)，收缩在问题4中处理；
      3. 初始温度和水分浓度在药材内部均匀分布；
      4. 因为 \(L/R=12.5\)，且题目要求的是“到药材中心的距离”，建立轴对称径向一维模型；
      5. 药材内部没有体热源，水分迁移用有效扩散模型描述；
      6. 附件1中的烘房水分浓度作为药材表面的有效平衡边界浓度；
      7. 附录3没有重新给出表面对流系数，因此沿用 \(h=25\ \mathrm{W/(m^2\cdot K)}\) 和 \(h_m=8\times10^{-7}\ \mathrm{m/s}\)。
      
      ## 3. 附件1边界数据的处理
      
      对附件1中的烘房温度 \(T_\infty(t)\) 和水分浓度 \(C_\infty(t)\) 分别作分段线性插值：
      
      \[
      y(t)=y_j+
      \frac{y_{j+1}-y_j}{t_{j+1}-t_j}(t-t_j),
      \qquad t_j\le t\le t_{j+1}.
      \]
      
      题目指定时刻的边界数据如下。
      
      | 时间/h | 时间/s | \(T_\infty/^\circ\mathrm C\) | \(C_\infty/(\mathrm{kg/kg})\) |
      |---:|---:|---:|---:|
      | 0.5 | 1800 | 41.5130 | 0.0331 |
      | 1.0 | 3600 | 47.4850 | 0.0427 |
      | 1.5 | 5400 | 49.1160 | 0.0473 |
      | 2.0 | 7200 | 49.8520 | 0.0489 |
      | 2.5 | 9000 | 50.1630 | 0.0498 |
      | 3.0 | 10800 | 50.1950 | 0.0498 |
      
      ## 4. 双向耦合控制方程
      
      ### 4.1 LaTeX源式
      
          \rho(C)c_p(C)\frac{\partial T}{\partial t}
          =\frac{1}{r}\frac{\partial}{\partial r}
          \left[rk(C)\frac{\partial T}{\partial r}\right],
      
          \frac{\partial C}{\partial t}
          =\frac{1}{r}\frac{\partial}{\partial r}
          \left[rD(T,C)\frac{\partial C}{\partial r}\right].
      
      ### 4.2 编译后的公式
      
      ![温度与水分耦合控制方程](</Users/a1523647308/overleaf modify/A题第二问_assets/formula-1.png>)
      
      第一行来自能量守恒和 Fourier 导热定律，描述药材内部的非稳态径向导热。第二行来自水分质量守恒和 Fick 扩散定律，描述内部水分从高浓度区域向低浓度区域迁移。
      
      温度方程中的三个热物性参数都由 \(C(r,t)\) 决定；水分方程中的 \(D\) 又由 \(T(r,t)\) 和 \(C(r,t)\) 共同决定。
      
      ## 5. 附录3经验公式
      
      ### 5.1 LaTeX源式
      
          \rho(C)=650+128C,
      
          c_p(C)=1450+2736\frac{C}{C+1},
      
          k(C)=0.21+0.38\frac{C}{C+1},
      
          D(T,C)=2.4\times10^{-3}
          \exp\left(-\frac{0.45}{C}\right)
          \exp\left[-\frac{3850}{T+273.15}\right].
      
      ### 5.2 编译后的公式
      
      ![附录3经验公式](</Users/a1523647308/overleaf modify/A题第二问_assets/formula-2.png>)
      
      | 参数 | 含义 | 单位 |
      |---|---|---|
      | \(\rho(C)\) | 药材密度 | kg/m³ |
      | \(c_p(C)\) | 药材比热容 | J/(kg·K) |
      | \(k(C)\) | 药材导热系数 | W/(m·K) |
      | \(D(T,C)\) | 有效水分扩散系数 | m²/s |
      | \(C\) | 干基含水率 | kg/kg |
      | \(T\) | 药材温度；代入 \(D\) 时使用K | °C或K |
      
      附录3中扩散系数公式的温度必须使用开尔文。
      
      ### 5.3 温标转换的LaTeX源式
      
          T_K=T_{^\circ\mathrm C}+273.15,
      
          D(T,C)=2.4\times10^{-3}e^{-0.45/C}e^{-3850/T_K}.
      
      ### 5.4 编译后的公式
      
      ![温标转换与扩散系数](</Users/a1523647308/overleaf modify/A题第二问_assets/formula-4.png>)
      
      如果把摄氏温度直接代入指数项，扩散系数会产生多个数量级的错误。
      
      ## 6. 初始条件和边界条件
      
      ### 6.1 LaTeX源式
      
          T(r,0)=28,\qquad C(r,0)=2.55,
      
          \left.\frac{\partial T}{\partial r}\right|_{r=0}=0,\qquad
          \left.\frac{\partial C}{\partial r}\right|_{r=0}=0,
      
          -k(C_s)\left.\frac{\partial T}{\partial r}\right|_{r=R}
          =h[T_s-T_\infty(t)],
      
          -D(T_s,C_s)\left.\frac{\partial C}{\partial r}\right|_{r=R}
          =h_m[C_s-C_\infty(t)].
      
      ### 6.2 编译后的公式
      
      ![初始条件和边界条件](</Users/a1523647308/overleaf modify/A题第二问_assets/formula-3.png>)
      
      其中 \(T_s=T(R,t)\)、\(C_s=C(R,t)\)。中心处两个零梯度条件来自圆柱轴对称性；表面温度满足 Newton 对流换热定律；表面水分满足内部扩散通量与对流传质通量连续。
      
      ## 7. 双向耦合关系
      
      \[
      C(r,t)
      \longrightarrow \rho(C),c_p(C),k(C)
      \longrightarrow T(r,t)
      \longrightarrow D(T,C)
      \longrightarrow C(r,t).
      \]
      
      具体含义是：
      
      1. 含水率改变，会改变药材密度、蓄热能力和导热能力；
      2. 温度升高会通过扩散系数加快内部水分迁移；
      3. 水分下降又会通过 \(\exp(-0.45/C)\) 改变扩散系数；
      4. 因此应在每个时间步内同步迭代温度场和水分场。
      
      ## 8. 数值计算过程
      
      ### 8.1 空间和时间离散
      
      在 \(0\le r\le0.02\ \mathrm m\) 上采用守恒型有限体积法，最终网格和时间步取
      
      \[
      \Delta r=5\times10^{-5}\ \mathrm m=0.005\ \mathrm{cm},
      \qquad
      \Delta t=0.5\ \mathrm s.
      \]
      
      每个环形控制体都满足“储存量变化＝内侧流入通量－外侧流出通量”。相邻网格界面的 \(k\) 和 \(D\) 采用调和平均，以保证界面通量连续。时间方向采用 Crank–Nicolson 格式。
      
      ### 8.2 每个时间步的耦合迭代
      
      已知第 \(n\) 个时刻的 \(T^n,C^n\) 后：
      
      1. 以 \(T^n,C^n\) 作为下一时刻的初始猜测；
      2. 根据当前 \(C\) 计算 \(\rho(C)、c_p(C)、k(C)\)；
      3. 代入附件1插值得到的 \(T_\infty(t)\)，求解温度方程；
      4. 将新温度转换成开尔文，根据新 \(T,C\) 计算 \(D(T,C)\)；
      5. 代入附件1插值得到的 \(C_\infty(t)\)，求解水分方程；
      6. 比较本次和上次迭代的 \(T,C\)；
      7. 若误差未达到要求，返回第2步继续迭代；
      8. 收敛后进入下一时间步。
      
      本次计算每个时间步最多经过4次 Picard 迭代即达到收敛条件。
      
      ### 8.3 输出抽取
      
      论文表格抽取 \(t=0.5,1.0,1.5,2.0,2.5,3.0\ \mathrm h\) 和
      \(r=0,0.5,1.0,1.5,2.0\ \mathrm{cm}\) 处的结果。制作 result2.xlsx 时，再从完整数值解中按每隔1 s、每隔0.1 cm抽取温度和水分浓度。
      
      ## 9. 网格和时间步独立性检验
      
      | 检验项目 | 两组设置 | 最大温度差/°C | 最大水分浓度差/(kg/kg) |
      |---|---|---:|---:|
      | 空间网格 | \(\Delta r=0.01\) cm 与 \(0.005\) cm，\(\Delta t=1\) s | \(8.25\times10^{-6}\) | \(7.47\times10^{-6}\) |
      | 时间步 | \(\Delta t=1\) s 与 \(0.5\) s，\(\Delta r=0.005\) cm | \(4.46\times10^{-7}\) | \(7.84\times10^{-9}\) |
      
      误差远小于题目要求的四位小数精度，因此以下结果采用加密解。
      
      ## 10. 最终计算结果
      
      ### 表3　3小时内药材的温度（°C）
      
      | 时间/h | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |
      |---:|---:|---:|---:|---:|---:|
      | 0.5 | 32.1892 | 32.3821 | 32.9659 | 33.9608 | 35.4130 |
      | 1.0 | 40.3816 | 40.5536 | 41.0605 | 41.8782 | 42.9976 |
      | 1.5 | 45.8468 | 45.9348 | 46.1930 | 46.6051 | 47.1401 |
      | 2.0 | 48.4502 | 48.4881 | 48.5984 | 48.7736 | 49.0033 |
      | 2.5 | 49.4670 | 49.4792 | 49.5137 | 49.5653 | 49.6609 |
      | 3.0 | 49.8495 | 49.8553 | 49.8746 | 49.9101 | 49.9664 |
      
      ### 表4　3小时内药材的水分浓度（kg/kg）
      
      | 时间/h | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |
      |---:|---:|---:|---:|---:|---:|
      | 0.5 | 2.5499 | 2.5489 | 2.5256 | 2.3257 | 1.6486 |
      | 1.0 | 2.5257 | 2.4948 | 2.3578 | 2.0230 | 1.4711 |
      | 1.5 | 2.3861 | 2.3256 | 2.1344 | 1.8020 | 1.3476 |
      | 2.0 | 2.1709 | 2.1084 | 1.9236 | 1.6259 | 1.2311 |
      | 2.5 | 1.9566 | 1.9006 | 1.7360 | 1.4720 | 1.1166 |
      | 3.0 | 1.7662 | 1.7165 | 1.5702 | 1.3333 | 1.0081 |
      
      ## 11. 结果分析
      
      0.5 h时，药材表面温度为 \(35.4130^\circ\mathrm C\)，中心温度为
      \(32.1892^\circ\mathrm C\)，表里温差约 \(3.22^\circ\mathrm C\)，说明预热初期内部温度梯度明显。
      
      随着烘房逐渐恒温，药材内部温差不断减小。3 h时中心温度为
      \(49.8495^\circ\mathrm C\)，表面温度为 \(49.9664^\circ\mathrm C\)，已经接近烘房温度
      \(50.1950^\circ\mathrm C\)，药材在热学意义上接近完成预热平衡。
      
      水分扩散明显慢于热扩散。0.5 h时表面含水率已降到 \(1.6486\ \mathrm{kg/kg}\)，中心仍为
      \(2.5499\ \mathrm{kg/kg}\)。3 h时中心含水率为 \(1.7662\ \mathrm{kg/kg}\)，表面为
      \(1.0081\ \mathrm{kg/kg}\)，内部仍存在明显水分梯度。
      
      第二问0.5 h的数值不应与第一问1800 s完全相同。第一问使用附录2中的常物性和
      \(D(C)\)，第二问则从 \(t=0\) 开始统一使用附录3中的变物性公式；二者的热扩散和水分扩散能力不同，结果存在差别是正常的。
      
      ## 12. 合理性检验
      
      1. 所有时刻均有中心温度低于表面温度，且表面温度低于同期烘房温度，热流方向正确；
      2. 所有时刻均有中心水分浓度高于表面水分浓度，水分由内部向表面迁移；
      3. 温度随时间升高，水分浓度随时间降低；
      4. 数值解没有超过外界温度，也没有出现负含水率或空间振荡；
      5. 3 h时温度场基本均匀，而水分梯度仍然明显，符合热扩散快于水分扩散的物理规律。
      
      ## 13. 可直接用于论文的结论
      
      第二问在第一问径向传热—传质模型的基础上，引入附录3给出的含水率相关热物性参数和温湿相关水分扩散系数，建立了非线性双向耦合模型。附件1提供随时间变化的烘房温度和水分浓度边界，有限体积法保证离散过程中的热量与水分通量守恒，Crank–Nicolson格式和Picard迭代用于求解变系数耦合方程。
      
      计算表明，药材温度在3 h内逐渐接近烘房温度，中心与表面的温差由0.5 h时约
      \(3.22^\circ\mathrm C\) 减小到3 h时约 \(0.12^\circ\mathrm C\)；水分迁移明显滞后，3 h时中心和表面的含水率分别为 \(1.7662\) 和 \(1.0081\ \mathrm{kg/kg}\)。前三小时主要完成温度平衡，但距离整体干燥要求仍有较大差距，这为问题3确定最终烘干时间提供了初始依据。
      
      ## 参考依据
      
      [1] 2026年高教社杯全国大学生数学建模竞赛A题、附件1与附录3。
      
      [2] Incropera, F. P., et al. *Fundamentals of Heat and Mass Transfer*. 7th ed., Wiley, 2011.
      
      [3] Crank, J. *The Mathematics of Diffusion*. 2nd ed., Clarendon Press, 1975.
      
      [4] Patankar, S. V. *Numerical Heat Transfer and Fluid Flow*. Hemisphere, 1980.
      
      ===== handoff/task2_handoff.md =====
      # A题问题二：融合型温度—水分双向耦合全流程数学模型
      
      ## 1. 问题定义
      
      药材近似为长
      
      \[
      L=25\ \mathrm{cm}
      \]
      
      、半径
      
      \[
      R=2\ \mathrm{cm}
      \]
      
      的圆柱体。烘干初始时刻为
      
      \[
      T(r,0)=28^\circ\mathrm C,
      \qquad
      C(r,0)=2.55\ \mathrm{kg/kg}.
      \]
      
      问题二要求建立整个烘干过程中药材内部温度场
      
      \[
      T(r,t)
      \]
      
      和干基含水率场
      
      \[
      C(r,t)
      \]
      
      的变化模型，并统一使用附录 3 给出的状态相关经验公式。
      
      计算区间为
      
      \[
      0\le t\le10800\ \mathrm s,
      \qquad
      0\le r\le0.02\ \mathrm m.
      \]
      
      附件 1 中烘房环境数据覆盖 \(0\sim14400\ \mathrm s\)，因此问题二前三小时的计算区间全部位于附件数据范围内。
      
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
      
      \[
      R=0.02\ \mathrm m
      \]
      
      不变，不考虑尺寸收缩。
      
      4. 初始温度和初始干基含水率在整个径向上均匀分布。
      
      5. 药材内部复杂孔隙结构和不同形态水分的迁移统一用题目给出的有效扩散系数 \(D(T,C)\) 表示。
      
      6. 密度、比热容、导热系数和水分扩散系数由局部当前状态决定。
      
      7. 烘房环境在药材圆柱侧表面上均匀分布。
      
      8. 表面对流换热系数和对流传质系数采用
      
      \[
      h=25\ \mathrm{W/(m^2\,K)},
      \]
      
      \[
      h_m=8\times10^{-7}\ \mathrm{m/s}.
      \]
      
      9. 附件 1 中的烘房水分浓度直接作为表面对流传质边界中的外部有效水分浓度
      
      \[
      C_\infty(t).
      \]
      
      10. 模型不包含蒸发潜热、辐射换热、内部热源、化学反应和相变动力学。
      
      11. 温度方程的局部储热项采用
      
      \[
      \rho(C)c_p(C)\frac{\partial T}{\partial t},
      \]
      
      不展开为包含物性时间导数的其他形式。
      
      ---
      
      ## 4. 变量与参数
      
      | 符号 | 含义 | 单位 |
      |---|---|---|
      | \(r\) | 距圆柱中心轴的径向距离 | m |
      | \(R\) | 药材半径 | m |
      | \(L\) | 药材长度 | m |
      | \(t\) | 时间 | s |
      | \(T(r,t)\) | 药材内部温度 | °C |
      | \(T_K(r,t)\) | 药材绝对温度 | K |
      | \(C(r,t)\) | 药材干基含水率 | kg/kg |
      | \(T_\infty(t)\) | 烘房温度 | °C |
      | \(C_\infty(t)\) | 烘房水分浓度 | kg/kg |
      | \(\rho(C)\) | 密度 | kg/m³ |
      | \(c_p(C)\) | 比热容 | J/(kg·K) |
      | \(k(C)\) | 导热系数 | W/(m·K) |
      | \(D(T,C)\) | 有效水分扩散系数 | m²/s |
      | \(h\) | 对流换热系数 | W/(m²·K) |
      | \(h_m\) | 对流传质系数 | m/s |
      
      ---
      
      ## 5. 烘房环境边界数据
      
      附件 1 给出离散时刻的烘房温度和水分浓度。
      
      对任一环境变量 \(y(t)\)，在相邻数据点
      
      \[
      (t_j,y_j),
      \qquad
      (t_{j+1},y_{j+1})
      \]
      
      之间采用分段线性插值：
      
      \[
      y(t)
      =
      y_j+
      \frac{y_{j+1}-y_j}{t_{j+1}-t_j}
      (t-t_j),
      \qquad
      t_j\le t\le t_{j+1}.
      \]
      
      由此分别得到
      
      \[
      T_\infty(t),
      \qquad
      C_\infty(t).
      \]
      
      在从 \(t^n\) 推进至 \(t^{n+1}\) 时，边界项使用
      
      \[
      T_\infty(t^{n+1}),
      \qquad
      C_\infty(t^{n+1}).
      \]
      
      ---
      
      ## 6. 附录 3 状态相关物性
      
      密度为
      
      \[
      \rho(C)=650+128C.
      \]
      
      比热容为
      
      \[
      c_p(C)
      =
      1450+2736\frac{C}{C+1}.
      \]
      
      导热系数为
      
      \[
      k(C)
      =
      0.21+0.38\frac{C}{C+1}.
      \]
      
      水分扩散系数为
      
      \[
      D(T,C)
      =
      2.4\times10^{-3}
      \exp\left(-\frac{0.45}{C}\right)
      \exp\left(-\frac{3850}{T_K}\right).
      \]
      
      其中
      
      \[
      T_K=T+273.15.
      \]
      
      因此 \(D\) 的计算使用绝对温度 Kelvin，温度场本身可以用摄氏度保存和输出。
      
      由这些经验式形成以下状态依赖关系：
      
      \[
      C
      \rightarrow
      \rho(C),c_p(C),k(C)
      \rightarrow
      T,
      \]
      
      以及
      
      \[
      T,C
      \rightarrow
      D(T,C)
      \rightarrow
      C.
      \]
      
      整体关系可写为
      
      \[
      C
      \rightarrow
      (\rho,c_p,k)
      \rightarrow
      T
      \rightarrow
      D
      \rightarrow
      C.
      \]
      
      ===== handoff/task2_xby_handoff.md =====
      # A 题问题二数值求解交接文档
      
      ## 1. 当前完成状态
      
      问题二已经完成固定半径圆柱的 3 h 热质耦合数值求解。当前交接基准是最新提交 `ed97452`（`修正问题二烘房边界数据`）以及该提交中的脚本和答案文件。
      
      已交付文件：
      
      - `solution/task2/script/solve_task2.py`：模型、有限体积离散、Picard 迭代、数值检查和答案输出脚本。
      - `solution/task2/answer/result2.xlsx`：按 `problem/附件/附件3/result2.xlsx` 模板生成的完整结果。
      - `solution/task2/answer/task2_all_results.csv`：包含全部时间和径向输出位置的 long-format 结果。
      
      求解范围为 `0 <= t <= 10800 s`、`0 <= r <= 0.02 m`。问题二没有引入尺寸收缩；附件 2 和问题四的收缩模型不属于本模型。
      
      ## 2. 问题二相对于问题一改变的内容
      
      问题二最大限度继承问题一的结构：
      
      - 药材近似为圆柱，采用径向一维模型；
      - 温度和水分均使用圆柱径向守恒方程；
      - `r=0` 使用中心对称零通量条件；
      - `r=R` 使用表面对流换热和对流传质 Robin 边界；
      - 继承相同的空间有限体积思想和附件 1 边界数据插值方式；问题二为实现逐步 Picard，时间离散改为后向欧拉并直接求解三对角系统；
      - 使用问题一的对流换热系数 `h=25 W/(m^2 K)` 和对流传质系数 `h_m=8e-7 m/s`。
      
      问题二只把问题一的固定物性替换为附录 3 给出的状态相关物性：`rho`、`cp`、`k`、`D` 在每个时间步、每个空间节点随当前 `T` 和 `C` 更新。由此形成以下状态依赖耦合：
      
      1. `C` 影响 `rho(C)`、`cp(C)` 和 `k(C)`，因此影响温度场；
      2. `T` 和 `C` 共同影响 `D(T,C)`，因此影响水分场；
      3. 代码通过每个时间步内的 Picard 迭代使这两个方向在当前时刻自洽。
      
      模型没有加入蒸发潜热源项，因此水分迁移不会以潜热形式直接出现在温度方程右端；热质耦合只通过上述动态物性发生。
      
      ## 3. 建模区域、变量和初始条件
      
      药材视为长度 `L=0.25 m`、半径 `R=0.02 m` 的均匀圆柱。只保留径向坐标，建模域为
      
      $$
      0\le r\le R,\qquad 0\le t\le 10800\ \mathrm{s}.
      $$
      
      状态变量为：
      
      - `T(r,t)`：药材温度，计算和输出均使用 `degC`；
      - `C(r,t)`：药材干基含水率，单位 `kg/kg`。
      
      初始条件在整个径向上均匀：
      
      $$
      T(r,0)=28\ ^\circ\mathrm{C},\qquad C(r,0)=2.55\ \mathrm{kg/kg}.
      $$
      
      长度 `L` 只作为题目几何参数记录。在径向守恒方程中，公共因子 `2 pi L` 在等式两侧约去，所以离散矩阵中不再显式出现 `L`。
      
      ## 4. 温度方程和热边界
      
      温度采用圆柱径向非稳态导热方程：
      
      $$
      \rho(C)c_p(C)\frac{\partial T}{\partial t}
      =\frac{1}{r}\frac{\partial}{\partial r}
      \left(k(C)r\frac{\partial T}{\partial r}\right).
      $$
      
      实现中将当前状态下的 `rho(C)*cp(C)` 作为温度时间导数前的瞬时储能系数，即离散项为 `rho*cp*dT/dt`；没有另外展开或加入 `T*d(rho*cp)/dt` 的物性时间导数项。这是当前问题二数值模型的明确实现约定。
      
      中心轴对称条件为：
      
      $$
      \left.\frac{\partial T}{\partial r}\right|_{r=0}=0.
      $$
      
      表面采用对流换热 Robin 条件。脚本采用的等价写法是：
      
      $$
      k\left.\frac{\partial T}{\partial r}\right|_{r=R}
      =h\left[T_{\mathrm{air}}(t)-T(R,t)\right],
      \qquad h=25\ \mathrm{W/(m^2 K)}.
      $$
      
      也可以写成标准外向热流形式：
      
      $$
      -k\left.\frac{\partial T}{\partial r}\right|_{r=R}
      =h\left[T(R,t)-T_{\mathrm{air}}(t)\right].
      $$
      
      当烘房温度高于药材表面温度时，脚本最后一个半控制体积的矩阵对角线上增加 `dt*R*h`，右端增加 `dt*R*h*T_air`，从而给药材提供正的净热输入。
      
      ## 5. 水分方程和传质边界
      
      水分采用状态相关扩散系数的圆柱径向扩散方程：
      
      $$
      \frac{\partial C}{\partial t}
      =\frac{1}{r}\frac{\partial}{\partial r}
      \left(rD(T,C)\frac{\partial C}{\partial r}\right).
      $$
      
      中心轴对称条件为：
      
      $$
      \left.\frac{\partial C}{\partial r}\right|_{r=0}=0.
      $$
      
      表面对流传质条件在脚本中写为：
      
      $$
      D\left.\frac{\partial C}{\partial r}\right|_{r=R}
      =h_m\left[C_{\mathrm{air}}(t)-C(R,t)\right],
      \qquad h_m=8\times10^{-7}\ \mathrm{m/s}.
      $$
      
      等价地，按外向通量写为：
      
      $$
      -D\left.\frac{\partial C}{\partial r}\right|_{r=R}
      =h_m\left[C(R,t)-C_{\mathrm{air}}(t)\right].
      $$
      
      通常 `C(R,t)>C_air(t)`，因此外向通量为正、药材内部水分下降。程序最后一个水分控制体积的矩阵对角线上增加 `dt*R*h_m`，右端增加 `dt*R*h_m*C_air`。
      
      ## 6. 附录 3 动态物性
      
      每个 Picard 迭代、每个径向节点都根据当前猜测状态重新计算：
      
      $$
      \rho=650+128C,
      $$
      
      $$
      c_p=1450+2736\frac{C}{C+1},
      $$
      
      $$
      k=0.21+0.38\frac{C}{C+1},
      $$
      
      $$
      D=2.4\times10^{-3}
      \exp\left(-\frac{0.45}{C}\right)
      \exp\left(-\frac{3850}{T_K}\right).
      $$
      
      单位分别为：
      
      - `rho`：`kg/m^3`；
      - `cp`：`J/(kg K)`；
      - `k`：`W/(m K)`；
      - `D`：`m^2/s`；
      - `C`：`kg/kg`。
      
      公式中的温度必须使用 Kelvin：
      
      $$
      T_K=T_{degC}+273.15.
      $$
      
      脚本的输出温度仍然是 `degC`，只有进入 `D` 公式的指数项时才加 `273.15`。`material_properties()` 对用于除法的 `C` 使用不小于 `1e-12` 的数值下限；Picard 收敛后对极小的数值负值作非负截断。这是数值保护，不是新的物性模型。
      
      ## 7. 模型假设和适用范围
      
      当前结果建立在以下假设上：
      
      1. 药材是均匀、各向同性的规则圆柱，空间上只考虑径向变化。
      2. 轴向梯度、两个端面的传热传质、内部孔隙的复杂结构和二维/三维效应均忽略。
      3. `R=2 cm` 在整个问题二计算期间保持不变，不考虑干燥收缩；收缩只应在问题四中按附件 2 和附录 4 单独建模。
      4. 初始温度 `28 degC` 和初始含水率 `2.55 kg/kg` 在整个半径内均匀。
      5. `h` 和 `h_m` 沿表面均匀，并在问题二计算中保持问题一的数值；没有重新反演或优化传递系数。
      6. 烘房温度和烘房水分浓度在药材表面空间上均匀；附件 1 中的 `水分浓度` 直接作为 `C_air(t)` 使用，不进行湿空气热力学换算。
      7. 不加入蒸发潜热、辐射换热、内部热源、化学反应或相变动力学；温度对水分的影响只通过附录 3 的 `D(T,C)` 体现。
      8. 不加入半径变化、移动网格或轴向流动等问题四内容。
      9. 当前使用附录 3 经验式覆盖整个 3 h 区间，不额外给动态物性做参数拟合。
      
      这些假设使问题二保持为固定几何下的热质耦合扩散问题；如果后续模型改变边界、几何或潜热处理，不能把新结果与当前结果直接混用。
      
      ## 8. 附件 1 烘房边界数据
      
      `load_air_data()` 读取 `problem/附件/附件1.xlsx` 中的三列：`时间`、`温度`、`水分浓度`。当前附件数据覆盖 `0--14400 s`，求解的 `0--10800 s` 完全位于数据范围内。
      
      读取后程序将三列转为数值、按时间排序，并对重复时间保留最后一条；随后使用 `numpy.interp` 对 `T_air(t)` 和 `C_air(t)` 进行分段线性插值。每个后向欧拉步在 `time_new_s` 处取边界值。
      
      因此，当前版本使用附件 1 的完整边界记录，包括 `1800 s` 之后的实际数据；不是把 `1800 s` 之后的边界冻结为 `1800 s` 末值。这个区别是最新提交 `ed97452` 修正的重点。
      
      ## 9. 径向有限体积离散
      
      ### 9.1 网格和控制体积
      
      内部节点包含 `r=0` 和 `r=R`：
      
      $$
      \Delta r=0.000125\ \mathrm{m}=0.0125\ \mathrm{cm},
      $$
      
      共 `161` 个节点。相邻节点面取算术中点：
      
      $$
      r_{i+1/2}=\frac{r_i+r_{i+1}}{2}.
      $$
      
      去掉公共因子 `2 pi L` 后，第 `i` 个控制体积的径向测度为：
      
      $$
      V_i^{(r)}=\int_{r_{i-1/2}}^{r_{i+1/2}}r\,dr
      =\frac{r_{i+1/2}^2-r_{i-1/2}^2}{2}.
      $$
      
      首尾节点是半控制体积，内部节点是完整控制体积。
      
      ### 9.2 内部面通量和面物性
      
      温度内部面的导热系数取相邻节点算术平均：
      
      $$
      k_{i+1/2}=\frac{k_i+k_{i+1}}{2},
      $$
      
      对应的径向导热通量系数为：
      
      $$
      G^T_{i+1/2}=k_{i+1/2}\frac{r_{i+1/2}}{\Delta r}.
      $$
      
      水分面扩散系数同样取算术平均：
      
      $$
      D_{i+1/2}=\frac{D_i+D_{i+1}}{2},
      \qquad
      G^C_{i+1/2}=D_{i+1/2}\frac{r_{i+1/2}}{\Delta r}.
      $$
      
      由相邻控制体积共享同一面通量，内部离散保持守恒。
      
      ### 9.3 中心和表面
      
      `r=0` 的内侧面因面半径为零，通量自然为零；代码不计算 `1/r`，因此不会出现中心除零。对常系数情形，这种半控制体积处理等价于中心极限中的
      
      $$
      \left.\frac{1}{r}\frac{\partial}{\partial r}
      \left(r\frac{\partial T}{\partial r}\right)\right|_{r=0}
      \approx\frac{4(T_1-T_0)}{\Delta r^2}.
      $$
      
      表面最后一个半控制体积的外侧面不再假设零通量，而是直接代入热/质 Robin 边界。这样既保留了半控制体积的几何测度，也使边界换热和传质项具有正确方向。
      
      线性系统均为三对角系统，使用 `scipy.linalg.solve_banded` 求解。
      
      ## 10. 后向欧拉和 Picard 非线性流程
      
      最终计算使用 `dt=1 s`、后向欧拉。对从 `t^n` 到 `t^(n+1)` 的每一步，流程如下：
      
      1. 令 `T^(0)=T^n`、`C^(0)=C^n`。
      2. 用当前猜测 `T^(m)`、`C^(m)` 计算所有节点的 `rho`、`cp`、`k`、`D`，并在相邻面取面系数。
      3. 冻结这些物性，分别组装并求解后向欧拉温度三对角系统和水分三对角系统，得到临时 `T^(m+1)`、`C^(m+1)`。
      4. 计算
      
         $$
         \max_i|T_i^{(m+1)}-T_i^{(m)}|,
         \qquad
         \max_i|C_i^{(m+1)}-C_i^{(m)}|.
      
      ===== handoff/task3_gjs_handoff.md =====
      # A题第三问：药材烘干时间的确定与水分浓度计算结果
      
      ## 1. 问题分析
      
      问题3不需要重新建立新的温度方程和水分方程，而是在问题2的非线性温度—水分双向耦合模型基础上继续计算，直到药材内部所有位置的水分浓度都低于规定值
      
      \[
      C_{\mathrm{lim}}=0.15\ \mathrm{kg/kg}.
      \]
      
      相较于问题2，问题3新增了三项工作：
      
      1. 将附件1只给到4 h的烘房边界条件合理延拓到整个干燥过程；
      2. 将“药材各处水分浓度低于0.15”转化为数学停止条件；
      3. 精确定位第一次达到干燥要求的时刻，并按每6 h输出表5。
      
      ## 2. 沿用问题2的双向耦合模型
      
      ### 2.1 LaTeX源式
      
          \rho(C)c_p(C)\frac{\partial T}{\partial t}
          =\frac1r\frac{\partial}{\partial r}
          \left[rk(C)\frac{\partial T}{\partial r}\right],
      
          \frac{\partial C}{\partial t}
          =\frac1r\frac{\partial}{\partial r}
          \left[rD(T,C)\frac{\partial C}{\partial r}\right].
      
      ### 2.2 编译后的公式
      
      ![问题2的双向耦合控制方程](</Users/a1523647308/overleaf modify/A题第二问_assets/formula-1.png>)
      
      附录3的材料参数仍为：
      
      ### 2.3 LaTeX源式
      
          \rho(C)=650+128C,
      
          c_p(C)=1450+2736\frac{C}{C+1},
      
          k(C)=0.21+0.38\frac{C}{C+1},
      
          D(T,C)=2.4\times10^{-3}
          \exp\left(-\frac{0.45}{C}\right)
          \exp\left(-\frac{3850}{T+273.15}\right).
      
      ### 2.4 编译后的公式
      
      ![附录3经验公式](</Users/a1523647308/overleaf modify/A题第二问_assets/formula-2.png>)
      
      扩散系数公式中的温度使用开尔文，即
      
      \[
      T_K=T_{^\circ\mathrm C}+273.15.
      \]
      
      初始条件、中心对称条件以及表面对流换热、传质条件也与问题2相同：
      
      ![初始条件和边界条件](</Users/a1523647308/overleaf modify/A题第二问_assets/formula-3.png>)
      
      其中继续采用
      
      \[
      R=0.02\ \mathrm m,\qquad
      h=25\ \mathrm{W/(m^2\cdot K)},\qquad
      h_m=8\times10^{-7}\ \mathrm{m/s}.
      \]
      
      ## 3. 烘房边界条件的长期延拓
      
      附件1只记录到
      
      \[
      14400\ \mathrm s=4\ \mathrm h,
      \]
      
      而烘干过程持续两至三天，因此必须确定4 h以后的烘房环境。
      
      附件1在 \(9000\sim14400\ \mathrm s\) 内已经进入稳定阶段。对该时间段统计得到：
      
      | 变量 | 平均值 | 标准差 | 最小值 | 最大值 |
      |---|---:|---:|---:|---:|
      | 烘房温度/°C | 50.0049 | 0.1540 | 49.7570 | 50.2460 |
      | 烘房水分浓度/(kg/kg) | 0.049994 | 0.000153 | 0.049750 | 0.050250 |
      
      因此，前4 h使用附件1逐点分段线性插值，4 h后使用稳定段平均值。
      
      ### 3.1 LaTeX源式
      
          T_\infty(t)=
          \begin{cases}
          \widetilde T_\infty(t),&0\le t\le14400\ {\rm s},\\
          50.0049^\circ{\rm C},&t>14400\ {\rm s},
          \end{cases}
      
          C_\infty(t)=
          \begin{cases}
          \widetilde C_\infty(t),&0\le t\le14400\ {\rm s},\\
          0.049994\ {\rm kg/kg},&t>14400\ {\rm s}.
          \end{cases}
      
      ### 3.2 编译后的公式
      
      ![烘房边界条件延拓](</Users/a1523647308/overleaf modify/A题第三问_assets/formula-1.png>)
      
      采用稳定阶段平均值可以削弱测量噪声的影响，比直接使用最后一个观测值更稳健。
      
      ## 4. 烘干结束条件
      
      题目要求“药材各处的水分浓度应低于0.15 kg/kg”，因此停止条件应写成整个空间上的最大值条件。
      
      ### 4.1 LaTeX源式
      
          t_{\rm dry}=
          \inf\left\{t>0:
          \max_{0\le r\le R}C(r,t)\le0.15\right\}.
      
      由于干燥过程中水分由内部向表面迁移，始终有
      
          \frac{\partial C}{\partial r}\le0,
      
      从而
      
          \max_{0\le r\le R}C(r,t)=C(0,t).
      
      所以实际停止条件可化为
      
          C(0,t_{\rm dry})=0.15.
      
      ### 4.2 编译后的公式
      
      ![烘干结束条件](</Users/a1523647308/overleaf modify/A题第三问_assets/formula-2.png>)
      
      计算时仍然检查全部径向网格点。整个计算过程中没有出现水分空间顺序反转，数值结果始终满足
      
      \[
      C(0,t)\ge C(r,t)\ge C(R,t),
      \]
      
      因此中心确实是最后达到干燥标准的位置。
      
      ## 5. 数值求解过程
      
      ### 5.1 离散方法
      
      空间方向继续采用守恒型径向有限体积法，时间方向采用Crank–Nicolson格式。每个时间步使用Picard迭代同步更新
      
      \[
      \rho(C),\quad c_p(C),\quad k(C),\quad D(T,C).
      \]
      
      每个时间步的求解顺序如下：
      
      1. 根据当前水分浓度更新 \(\rho,c_p,k\)；
      2. 求解温度方程；
      3. 把温度转换为开尔文并更新 \(D(T,C)\)；
      4. 求解水分方程；
      5. 重复上述过程，直到温度和水分浓度同时收敛；
      6. 检查全部网格点是否满足 \(C\le0.15\)；
      7. 未满足则进入下一时间步，满足则定位结束时刻。
      
      最细网格计算中，每个时间步最多经过8次Picard迭代达到收敛。
      
      ### 5.2 分阶段时间步
      
      前4 h烘房环境变化较快，取
      
      \[
      \Delta t=2\ \mathrm s.
      \]
      
      4 h后烘房进入稳定阶段，温湿度和水分场变化明显变慢，取
      
      \[
      \Delta t=10\ \mathrm s.
      \]
      
      为了验证时间步误差，另用前4 h为1 s、4 h后为5 s进行复算，得到的结束时刻仅相差
      
      \[
      0.0073\ \mathrm s,
      \]
      
      说明时间离散误差可以忽略。
      
      ### 5.3 阈值时刻定位
      
      若相邻两个时间层满足
      
      \[
      C(0,t_n)>0.15,\qquad C(0,t_{n+1})<0.15,
      \]
      
      则在线性时间插值下定位结束时刻。
      
      #### LaTeX源式
      
          t_{\rm dry}\approx t_n+
          \frac{C(0,t_n)-0.15}
          {C(0,t_n)-C(0,t_{n+1})}
          (t_{n+1}-t_n).
      
      #### 编译后的公式
      
      ![结束时刻插值公式](</Users/a1523647308/overleaf modify/A题第三问_assets/formula-3.png>)
      
      ## 6. 空间网格收敛检验
      
      干燥后期含水率下降使 \(D(T,C)\) 显著减小，药材表面附近形成较陡的水分梯度。因此，问题3所需空间网格应比问题2更细。
      
      | 径向区间数 \(N\) | \(\Delta r\)/cm | 计算得到的结束时间/h | 相对上一网格变化/h |
      |---:|---:|---:|---:|
      | 200 | 0.01000 | 58.9449 | — |
      | 400 | 0.00500 | 57.6779 | 1.2671 |
      | 800 | 0.00250 | 57.5031 | 0.1748 |
      | 1600 | 0.00125 | 57.4719 | 0.0312 |
      
      可以看到，网格持续加密后结束时刻逐渐稳定。最终结果采用 \(N=1600\) 的最细网格。最后两级网格的差为0.0312 h，约1.87 min，可视为当前离散下的保守数值不确定度。
      
      ## 7. 烘干结束时间
      
      最细网格计算得到
      
      \[
      \boxed{
      t_{\mathrm{dry}}=57.4719\ \mathrm h
      }
      \]
      
      即约为
      
      \[
      2\ \mathrm d\ 9\ \mathrm h\ 28\ \mathrm{min}.
      \]
      
      实用工艺上可向上取整为
      
      \[
      \boxed{57.5\ \mathrm h}
      \]
      
      以保证药材中心不会高于规定水分浓度。
      
      ## 8. 表5：药材烘干过程的水分浓度
      
      单位：kg/kg。
      
      | 时间/h | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |
      |---:|---:|---:|---:|---:|---:|
      | 6 | 1.0169 | 0.9881 | 0.9015 | 0.7550 | 0.5328 |
      | 12 | 0.4561 | 0.4431 | 0.4030 | 0.3297 | 0.1642 |
      | 18 | 0.2988 | 0.2915 | 0.2687 | 0.2253 | 0.0845 |
      | 24 | 0.2378 | 0.2327 | 0.2167 | 0.1855 | 0.0665 |
      | 30 | 0.2058 | 0.2018 | 0.1892 | 0.1641 | 0.0598 |
      | 36 | 0.1859 | 0.1825 | 0.1718 | 0.1504 | 0.0566 |
      | 42 | 0.1721 | 0.1691 | 0.1597 | 0.1407 | 0.0548 |
      | 48 | 0.1618 | 0.1592 | 0.1507 | 0.1334 | 0.0537 |
      | 54 | 0.1539 | 0.1514 | 0.1436 | 0.1277 | 0.0530 |
      | 烘干结束：57.4719 | 0.1500 | 0.1477 | 0.1402 | 0.1249 | 0.0527 |
      
      
      ===== handoff/task3_xby_handoff.md =====
      # Codex conversation
      
      ## User
      
      你现在负责 2026CUMCM 项目的 A 题问题三真实求解。你的唯一目标是得到可信的最终数值答案，并实际生成题目要求的结果文件。不要停留在讨论、方案建议或论文写作阶段。
      
      【一、你的身份与工作方式】
      
      你是 5.6-sol medium，作为整个任务的根模型。
      
      你的职责仅限于：
      1. 理解我的要求和题目；
      2. 阅读现有问题一、问题二的模型、代码和结果；
      3. 决定问题三应该怎样继承问题二；
      4. 给 luna-worker 下达明确、范围有限的任务；
      5. 审查 luna-worker 的实现和数值结果；
      6. 判断结果是否合理，发现问题后继续派 luna-worker 修正；
      7. 最终汇总真实求解结果。
      
      代码编写、修改 Python、运行求解器、生成 CSV/XLSX、数值实验、调试等实际执行工作，应主动派给 luna-worker 完成。
      
      不要自己大段写实现代码。
      不要为了显得复杂而建立大量 agent。
      原则上一个执行中的 luna-worker 完成一个明确任务即可，需要修改时继续派 worker 处理。
      
      除非遇到真正无法自动解决的阻塞问题，否则不要频繁询问我，也不要每一步等待确认。
      
      【二、项目目录】
      
      当前项目根目录为：
      
      2026CUMCM
      ├── context
      │   └── context-task1-1_xby.md
      ├── handoff
      │   ├── task1_gjs_handoff.md
      │   └── task1_xby_handoff.md
      ├── problem
      │   ├── A题.md
      │   ├── A题.pdf
      │   └── 附件
      │       ├── 附件1.xlsx
      │       ├── 附件2.xlsx
      │       └── 附件3
      │           ├── result1.xlsx
      │           ├── result2.xlsx
      │           ├── result3.xlsx
      │           └── result4.xlsx
      └── solution
          └── task1
              ├── answer
              │   ├── task1_key_results.csv
              │   └── task1_result.csv
              └── script
                  └── solve_task1.py
      
      开始后先执行 pwd、git status，并检查仓库当前真实目录结构。
      
      尤其要主动搜索仓库里是否已经存在：
      - solution/task2/
      - task2 求解脚本
      - task2 的 answer/
      - task2 的 context/handoff
      - task2 的最新 Git 提交
      
      我给出的目录可能不是此刻仓库的完整最新状态，以实际 Git 工作区为准。
      
      【三、开始前必须阅读的内容】
      
      首先阅读：
      
      1. problem/A题.md
      2. 与问题二有关的最新 context / handoff，如果仓库中存在
      3. solution/task2 中的问题二求解代码和结果，如果存在
      4. 必要时参考 solution/task1，但不要重新求问题一
      
      附件本身没有问题。
      
      不要浪费时间检查附件是否合法、是否损坏、格式是否规范、是否存在版权问题。
      不要对附件做所谓的防御性验证。
      直接把题目和附件作为可信输入使用。
      
      尤其禁止修改 problem/ 下的任何原始文件。
      
      【四、问题三的数学任务】
      
      问题三要求：
      
      药材各处水分浓度均低于
      
      C < 0.15 kg/kg
      
      时认为烘干完成。
      
      需要确定药材烘干所需要的时间，单位为 h。
      
      问题三继续采用问题二和问题三统一规定的附录 3 经验公式：
      
      ρ = 650 + 128C
      
      cp = 1450 + 2736 * C/(C+1)
      
      k = 0.21 + 0.38 * C/(C+1)
      
      D = 2.4×10^-3 * exp(-0.45/C) * exp(-3850/T)
      
      其中 T 必须使用 K。
      
      问题三不是重新建立一套独立模型。
      
      必须优先直接继承问题二已经确定的：
      - 温度控制方程
      - 水分扩散方程
      - 圆柱径向一维模型
      - 初始条件
      - 表面对流换热条件
      - 表面对流传质条件
      - 烘房温度和水分浓度随时间的处理
      - 预热阶段与恒温干燥阶段衔接方式
      - 空间离散方法
      - 时间积分方法
      - 非线性参数更新方式
      
      问题三的本质是在问题二求解器基础上，把模拟时间继续向后延长，直到满足终止条件。
      
      不得因为进入问题三就重新选择一套不同的 PDE、边界条件或数值算法。
      
      如果当前仓库中存在多个问题二版本，以最新、已经实际运行并输出最终问题二结果的版本作为基线，同时结合 Git 历史确认。
      
      【五、终止条件】
      
      真正的烘干结束条件是：
      
      max_r C(r,t) < 0.15 kg/kg
      
      也就是整个药材内部所有计算位置都已经低于 0.15。
      
      不要仅仅检查表面。
      不要仅仅因为平均含水率低于 0.15 就停止。
      
      虽然理论上中心通常可能是最后达到要求的位置，但程序仍应直接检查完整径向水分场，不要把“中心一定最后干”硬编码成终止条件。
      
      从 t=0 开始延续问题二模型进行求解，不要把问题三错误地当成“从第 3 h 重新开始一个新问题”。
      
      可以复用问题二在前 3 h 已经计算得到的状态或直接一次性积分完整时间区间，两种实现只要数学上连续一致即可。
      
      【六、需要生成的文件】
      
      新建：
      
      solution/task3/
      ├── script/
      │   └── solve_task3.py
      └── answer/
          ├── result3.xlsx
          └── task3_all_results.csv
      
      原则上只需要一个 solve_task3.py。
      不要为了这个任务建立大型框架。
      
      1. result3.xlsx
      
      必须以：
      
      problem/附件/附件3/result3.xlsx
      
      为模板。
      
      禁止覆盖原模板。
      
      复制模板结构后写入：
      
      solution/task3/answer/result3.xlsx
      
      按照 A题.md 的要求：
      
      - 保存药材内部水分浓度
      - A 列为时间，单位 s
      - 第一行为到药材中心距离，单位 cm
      - 时间间隔为 60 s
      - 距离间隔为 0.1 cm
      - 半径范围 0～2 cm
      - 一直保存到烘干结束附近
      - 所有结果保留四位小数
      
      如果最终烘干时刻不是 60 s 的整数倍：
      完整结果文件仍按照题目规定的 60 s 间隔保存；
      最终烘干时间另外准确报告，不要为了让时间落在 60 s 网格上人为改变终止条件。
      
      2. task3_all_results.csv
      
      生成：
      
      solution/task3/answer/task3_all_results.csv
      
      CSV 要包含问题三完整答案，至少采用清晰的长表结构：
      
      time_s,radius_cm,moisture_kgkg
      
      要求：
      - t 从 0 到烘干结束
      - 输出时间间隔 60 s
      - radius_cm = 0,0.1,0.2,...,2.0
      - 数值保留四位小数
      
      CSV 与 result3.xlsx 中对应位置的数据必须一致。
      
      【七、论文表 5 所需结果】
      
      除了完整结果，还必须实际提取题目表 5 所需的数据。
      
      时间：
      
      6 h
      12 h
      18 h
      24 h
      30 h
      ……
      
      每隔 6 h 一行，一直列到烘干结束前。
      
      空间位置：
      
      0 cm
      0.5 cm
      1.0 cm
      1.5 cm
      2.0 cm
      
      最后额外给出：
      
      “烘干结束时间”
      
      这一行对应上述 5 个位置的水分浓度。
      
      最终汇报中直接打印出完整的表 5 数值，使我可以直接拿去写论文。
      
      所有数值保留四位小数。
      
      同时明确报告：
      
      烘干结束时间 = ____ h
      
      不要只说“大约两天”或给一个时间范围。
      
      【八、数值求解原则】
      
      核心原则是继承问题二，而不是重新调参。
      
      如果问题二已经使用固定的：
      - Δr
      - 时间步
      - Crank–Nicolson
      - BDF
      - Picard
      - 算术平均或调和平均
      - 插值方式
      
      问题三全部保持一致，除非长时间积分出现明确的数值错误。
      
      ===== solution/task2/script/solve_task2.py =====
      """A题问题二：动态物性圆柱径向热质耦合求解。
      
      模型沿用问题一的圆柱径向守恒有限体积离散，时间方向使用后向欧拉。
      问题二的 rho、cp、k、D 在每个时间步的 Picard 迭代中由当前 T、C 更新，
      从而得到当前时间步内的自洽隐式解。内部网格含 r=0 和 r=R 两个节点，
      两端为半控制体积；输出网格为每 1 s、每 0.1 cm。
      """
      
      from __future__ import annotations
      
      import argparse
      import csv
      import time as wall_time
      from copy import copy
      from pathlib import Path
      from typing import Any
      
      import numpy as np
      import pandas as pd
      from openpyxl import load_workbook
      from scipy.linalg import solve_banded
      
      
      # 几何、初始状态和输出约定（内部长度统一使用 m）。
      RADIUS_M = 0.02
      LENGTH_M = 0.25  # 一维径向守恒式中约去，保留作题目参数记录。
      BASE_DR_M = 0.000125
      INITIAL_TEMPERATURE_C = 28.0
      INITIAL_MOISTURE_KGKG = 2.55
      FINAL_TIME_S = 10800.0
      OUTPUT_DT_S = 1.0
      OUTPUT_RADIUS_CM = np.arange(0.0, 2.0000001, 0.1)
      
      # 问题一沿用的边界传递参数。
      HEAT_TRANSFER_W_M2_K = 25.0
      MASS_TRANSFER_M_S = 8.0e-7
      
      # Picard 收敛参数。绝对阈值足以保证四位小数输出稳定，同时避免无意义地
      # 将迭代压到机器精度。
      PICARD_TOL_T_C = 1.0e-8
      PICARD_TOL_C_KGKG = 1.0e-10
      PICARD_MAX_ITER = 50
      
      DEFAULT_DATA_PATH = (
          Path(__file__).resolve().parents[3] / "problem" / "附件" / "附件1.xlsx"
      )
      DEFAULT_TEMPLATE_PATH = (
          Path(__file__).resolve().parents[3]
          / "problem"
          / "附件"
          / "附件3"
          / "result2.xlsx"
      )
      DEFAULT_XLSX_PATH = Path(__file__).resolve().parents[1] / "answer" / "result2.xlsx"
      DEFAULT_CSV_PATH = (
          Path(__file__).resolve().parents[1] / "answer" / "task2_all_results.csv"
      )
      
      
      def load_air_data(
          path: str | Path = DEFAULT_DATA_PATH,
          required_end_s: float = FINAL_TIME_S,
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
          """读取附件1的全部烘房边界数据，供求解区间内分段线性插值。"""
      
          frame = pd.read_excel(Path(path))
          column_map = {str(column).strip(): column for column in frame.columns}
          required = ("时间", "温度", "水分浓度")
          missing = [column for column in required if column not in column_map]
          if missing:
              raise ValueError(f"附件1缺少必需列: {missing}; 实际列为 {list(frame.columns)!r}")
      
          selected = frame[[column_map[column] for column in required]].copy()
          selected.columns = required
          for column in required:
              selected[column] = pd.to_numeric(selected[column], errors="raise")
          selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")
      
          time_s = selected["时间"].to_numpy(dtype=float)
          air_temperature_C = selected["温度"].to_numpy(dtype=float)
          air_moisture_kgkg = selected["水分浓度"].to_numpy(dtype=float)
          if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
              raise ValueError("附件1时间必须包含至少两个严格递增时间点")
          if time_s[0] > 1.0e-10 or time_s[-1] < required_end_s - 1.0e-10:
              raise ValueError(f"附件1烘房边界数据未覆盖 0--{required_end_s:g} s")
          if not np.all(np.isfinite(np.column_stack((time_s, air_temperature_C, air_moisture_kgkg)))):
              raise ValueError("附件1烘房边界数据包含非有限数值")
          return time_s, air_temperature_C, air_moisture_kgkg
      
      
      def control_volume_geometry(
          radius_m: float = RADIUS_M, dr_m: float = BASE_DR_M
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
          """返回含两端半控制体积的节点、面和径向测度。"""
      
          if radius_m <= 0.0 or dr_m <= 0.0:
              raise ValueError("半径和空间步长必须为正")
          n_intervals = int(round(radius_m / dr_m))
          if not np.isclose(n_intervals * dr_m, radius_m, rtol=0.0, atol=1.0e-12):
              raise ValueError("当前网格要求半径可由整数个 dr 划分")
          radii_m = np.linspace(0.0, radius_m, n_intervals + 1)
          faces_m = 0.5 * (radii_m[:-1] + radii_m[1:])
          radial_measure_m2 = np.empty_like(radii_m)
          radial_measure_m2[0] = 0.5 * faces_m[0] ** 2
          radial_measure_m2[1:-1] = 0.5 * (faces_m[1:] ** 2 - faces_m[:-1] ** 2)
          radial_measure_m2[-1] = 0.5 * (radius_m**2 - faces_m[-1] ** 2)
          return radii_m, faces_m, radial_measure_m2
      
      
      def material_properties(
          temperature_C: np.ndarray, moisture_kgkg: np.ndarray
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
          """按当前 Picard 状态计算 rho、cp、k 和 D（SI 单位）。"""
      
          temperature_C = np.asarray(temperature_C, dtype=float)
          moisture_kgkg = np.asarray(moisture_kgkg, dtype=float)
          concentration = np.maximum(moisture_kgkg, 1.0e-12)
          temperature_K = temperature_C + 273.15
          if np.any(temperature_K <= 0.0):
              raise ValueError("动态物性计算遇到非正 Kelvin 温度")
      
          rho = 650.0 + 128.0 * concentration
          cp = 1450.0 + 2736.0 * concentration / (concentration + 1.0)
          k = 0.21 + 0.38 * concentration / (concentration + 1.0)
          diffusivity = 2.4e-3 * np.exp(-0.45 / concentration) * np.exp(
              -3850.0 / temperature_K
          )
          return rho, cp, k, diffusivity
      
      
      def _solve_tridiagonal(
          lower: np.ndarray, diagonal: np.ndarray, upper: np.ndarray, rhs: np.ndarray
      ) -> np.ndarray:
          """解三对角线性系统，矩阵系数均为当前 Picard 冻结值。"""
      
          n = diagonal.size
          banded = np.zeros((3, n), dtype=float)
          banded[0, 1:] = upper
          banded[1, :] = diagonal
          banded[2, :-1] = lower
          return solve_banded((1, 1), banded, rhs, check_finite=False)
      
      
      def _solve_temperature_linear(
          old_temperature_C: np.ndarray,
          guess_temperature_C: np.ndarray,
          guess_moisture_kgkg: np.ndarray,
          radial_measure_m2: np.ndarray,
          faces_m: np.ndarray,
          dr_m: float,
          dt_s: float,
          air_temperature_C: float,
      ) -> np.ndarray:
          """在给定 Picard 物性下求解一个后向欧拉温度步。"""
      
          rho, cp, conductivity, _ = material_properties(
              guess_temperature_C, guess_moisture_kgkg
          )
          storage = rho * cp * radial_measure_m2
          face_k = 0.5 * (conductivity[:-1] + conductivity[1:])
          conductance = face_k * faces_m / dr_m
      
          diagonal = storage.copy()
          diagonal[0] += dt_s * conductance[0]
          diagonal[1:-1] += dt_s * (conductance[:-1] + conductance[1:])
          diagonal[-1] += dt_s * (
              conductance[-1] + RADIUS_M * HEAT_TRANSFER_W_M2_K
          )
          lower = -dt_s * conductance.copy()
          upper = -dt_s * conductance.copy()
          rhs = storage * old_temperature_C
          rhs[-1] += dt_s * RADIUS_M * HEAT_TRANSFER_W_M2_K * air_temperature_C
          return _solve_tridiagonal(lower, diagonal, upper, rhs)
      
      
      def _solve_moisture_linear(
          old_moisture_kgkg: np.ndarray,
          guess_temperature_C: np.ndarray,
          guess_moisture_kgkg: np.ndarray,
          radial_measure_m2: np.ndarray,
          faces_m: np.ndarray,
          dr_m: float,
          dt_s: float,
          air_moisture_kgkg: float,
      ) -> np.ndarray:
          """在给定 Picard 物性下求解一个后向欧拉水分步。"""
      
          _, _, _, diffusivity = material_properties(
              guess_temperature_C, guess_moisture_kgkg
          )
          storage = radial_measure_m2
          face_D = 0.5 * (diffusivity[:-1] + diffusivity[1:])
          conductance = face_D * faces_m / dr_m
      
          diagonal = storage.copy()
          diagonal[0] += dt_s * conductance[0]
          diagonal[1:-1] += dt_s * (conductance[:-1] + conductance[1:])
          diagonal[-1] += dt_s * (conductance[-1] + RADIUS_M * MASS_TRANSFER_M_S)
          lower = -dt_s * conductance.copy()
          upper = -dt_s * conductance.copy()
          rhs = storage * old_moisture_kgkg
          rhs[-1] += dt_s * RADIUS_M * MASS_TRANSFER_M_S * air_moisture_kgkg
          return _solve_tridiagonal(lower, diagonal, upper, rhs)
      
      
      def _picard_step(
          old_temperature_C: np.ndarray,
          old_moisture_kgkg: np.ndarray,
          time_new_s: float,
          dt_s: float,
          radial_measure_m2: np.ndarray,
          faces_m: np.ndarray,
          dr_m: float,
          air_temperature_C: float,
          air_moisture_kgkg: float,
          tol_temperature_C: float = PICARD_TOL_T_C,
          tol_moisture_kgkg: float = PICARD_TOL_C_KGKG,
          max_iter: int = PICARD_MAX_ITER,
      ) -> tuple[np.ndarray, np.ndarray, int, float, float]:
          """使用当前时间步内的 Picard 外迭代求 T、C 自洽解。"""
      
          # time_new_s 同时用于异常信息，明确边界取值属于当前时间步。
          guess_temperature_C = old_temperature_C.copy()
          guess_moisture_kgkg = old_moisture_kgkg.copy()
          last_delta_temperature = np.inf
          last_delta_moisture = np.inf
      
          for iteration in range(1, max_iter + 1):
              new_temperature_C = _solve_temperature_linear(
                  old_temperature_C,
                  guess_temperature_C,
                  guess_moisture_kgkg,
                  radial_measure_m2,
                  faces_m,
                  dr_m,
                  dt_s,
                  air_temperature_C,
              )
              new_moisture_kgkg = _solve_moisture_linear(
                  old_moisture_kgkg,
                  guess_temperature_C,
                  guess_moisture_kgkg,
                  radial_measure_m2,
                  faces_m,
                  dr_m,
                  dt_s,
                  air_moisture_kgkg,
              )
              last_delta_temperature = float(
                  np.max(np.abs(new_temperature_C - guess_temperature_C))
              )
              last_delta_moisture = float(
                  np.max(np.abs(new_moisture_kgkg - guess_moisture_kgkg))
              )
              if (
                  last_delta_temperature <= tol_temperature_C
                  and last_delta_moisture <= tol_moisture_kgkg
              ):
                  if np.min(new_moisture_kgkg) < -1.0e-10:
                      raise RuntimeError("Picard 步得到明显负水分浓度")
      
      ===== solution/task3/script/solve_task3.py =====
      """A题问题三：继承问题二模型的长期烘干求解器。
      
      问题三从 t=0 连续推进问题二的固定半径、动态物性热质耦合模型，
      在每个 dt=1 s 的内部时间步检查完整径向水分场，首次满足
      max_r C(r,t) < 0.15 kg/kg 时停止。输出文件只保留题目要求的
      60 s 时间网格；精确终止时刻和终止状态用于表5及验证报告。
      """
      
      from __future__ import annotations
      
      import argparse
      import csv
      import sys
      import time as wall_time
      from copy import copy
      from pathlib import Path
      from typing import Any
      
      import numpy as np
      import pandas as pd
      from openpyxl import load_workbook
      
      
      # 直接复用问题二的数值核心和模型常量，不改变问题二算法。
      TASK2_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "task2" / "script"
      if str(TASK2_SCRIPT_DIR) not in sys.path:
          sys.path.insert(0, str(TASK2_SCRIPT_DIR))
      import solve_task2 as task2  # noqa: E402
      
      
      RADIUS_M = task2.RADIUS_M
      BASE_DR_M = task2.BASE_DR_M
      INITIAL_TEMPERATURE_C = task2.INITIAL_TEMPERATURE_C
      INITIAL_MOISTURE_KGKG = task2.INITIAL_MOISTURE_KGKG
      HEAT_TRANSFER_W_M2_K = task2.HEAT_TRANSFER_W_M2_K
      MASS_TRANSFER_M_S = task2.MASS_TRANSFER_M_S
      PICARD_MAX_ITER = task2.PICARD_MAX_ITER
      OUTPUT_RADIUS_CM = task2.OUTPUT_RADIUS_CM.copy()
      
      TIME_STEP_S = 1.0
      OUTPUT_DT_S = 60.0
      TABLE5_DT_S = 6.0 * 3600.0
      DRYING_THRESHOLD_KGKG = 0.15
      # 题目说明过程一般持续2--3天；上限仅用于防止异常情况下无限循环。
      DEFAULT_MAX_TIME_S = 7.0 * 24.0 * 3600.0
      
      REPO_ROOT = Path(__file__).resolve().parents[3]
      DEFAULT_DATA_PATH = REPO_ROOT / "problem" / "附件" / "附件1.xlsx"
      DEFAULT_TEMPLATE_PATH = REPO_ROOT / "problem" / "附件" / "附件3" / "result3.xlsx"
      DEFAULT_XLSX_PATH = Path(__file__).resolve().parents[1] / "answer" / "result3.xlsx"
      DEFAULT_CSV_PATH = (
          Path(__file__).resolve().parents[1] / "answer" / "task3_all_results.csv"
      )
      DEFAULT_TASK2_CSV_PATH = (
          REPO_ROOT / "solution" / "task2" / "answer" / "task2_all_results.csv"
      )
      
      KEY_RADIUS_INDICES = np.array([0, 5, 10, 15, 20], dtype=int)
      
      
      def _output_indices(radii_m: np.ndarray) -> np.ndarray:
          """取得题目要求的0--2 cm、每0.1 cm输出位置。"""
      
          target_m = OUTPUT_RADIUS_CM / 100.0
          indices = np.array([int(np.argmin(np.abs(radii_m - r))) for r in target_m])
          if not np.allclose(radii_m[indices], target_m, atol=1.0e-12, rtol=0.0):
              raise ValueError("当前内部网格不能精确包含题目要求的0.1 cm输出位置")
          return indices
      
      
      def solve_task3(
          data_path: str | Path = DEFAULT_DATA_PATH,
          max_time_s: float = DEFAULT_MAX_TIME_S,
          time_step_s: float = TIME_STEP_S,
          output_dt_s: float = OUTPUT_DT_S,
          dr_m: float = BASE_DR_M,
          progress: bool = False,
      ) -> dict[str, Any]:
          """从 t=0 连续推进问题二状态，直到完整场严格低于阈值。"""
      
          if max_time_s <= 0.0 or time_step_s <= 0.0 or output_dt_s <= 0.0:
              raise ValueError("时间上限、时间步和输出间隔必须为正")
          max_steps_float = max_time_s / time_step_s
          max_steps = int(np.floor(max_steps_float + 1.0e-10))
          if max_steps < 1 or not np.isclose(max_steps_float, max_steps, atol=1.0e-10):
              raise ValueError("时间上限必须由整数个内部时间步组成")
          output_ratio = output_dt_s / time_step_s
          output_stride = int(round(output_ratio))
          if not np.isclose(output_ratio, output_stride, atol=1.0e-10):
              raise ValueError("输出间隔必须是内部时间步的整数倍")
      
          # 附件1只覆盖初期，np.interp 在末点以后按题目要求保持最后边界值。
          air_time_s, air_temperature, air_moisture = task2.load_air_data(
              data_path, required_end_s=0.0
          )
          air_temperature_interp = lambda t: float(np.interp(t, air_time_s, air_temperature))
          air_moisture_interp = lambda t: float(np.interp(t, air_time_s, air_moisture))
      
          radii_m, faces_m, radial_measure_m2 = task2.control_volume_geometry(RADIUS_M, dr_m)
          output_indices = _output_indices(radii_m)
          n_nodes = radii_m.size
      
          current_temperature = np.full(n_nodes, INITIAL_TEMPERATURE_C, dtype=float)
          current_moisture = np.full(n_nodes, INITIAL_MOISTURE_KGKG, dtype=float)
      
          sampled_times: list[float] = [0.0]
          sampled_moisture: list[np.ndarray] = [current_moisture[output_indices].copy()]
          first_3h_moisture = np.full((10801, output_indices.size), np.nan, dtype=float)
          first_3h_moisture[0] = current_moisture[output_indices]
          table5_times: list[float] = []
          table5_values: list[np.ndarray] = []
      
          iteration_counts: list[int] = []
          picard_delta_temperature: list[float] = []
          picard_delta_moisture: list[float] = []
          max_positive_step_change = -np.inf
          max_abs_step_change = 0.0
          min_internal_moisture = float(np.min(current_moisture))
          max_internal_moisture = float(np.max(current_moisture))
          previous_max_moisture = float(np.max(current_moisture))
          termination_time_s: float | None = None
          termination_state: np.ndarray | None = None
          termination_previous_state: np.ndarray | None = None
          termination_previous_max = np.nan
          termination_max = np.nan
      
          for step in range(1, max_steps + 1):
              time_new_s = step * time_step_s
              previous_moisture = current_moisture
              (
                  current_temperature,
                  current_moisture,
                  iterations,
                  delta_temperature,
                  delta_moisture,
              ) = task2._picard_step(
                  current_temperature,
                  previous_moisture,
                  time_new_s,
                  time_step_s,
                  radial_measure_m2,
                  faces_m,
                  dr_m,
                  air_temperature_interp(time_new_s),
                  air_moisture_interp(time_new_s),
              )
              iteration_counts.append(int(iterations))
              picard_delta_temperature.append(float(delta_temperature))
              picard_delta_moisture.append(float(delta_moisture))
      
              change = current_moisture - previous_moisture
              max_positive_step_change = max(max_positive_step_change, float(np.max(change)))
              max_abs_step_change = max(max_abs_step_change, float(np.max(np.abs(change))))
              min_internal_moisture = min(min_internal_moisture, float(np.min(current_moisture)))
              max_internal_moisture = max(max_internal_moisture, float(np.max(current_moisture)))
      
              if time_new_s <= 10800.0 + 1.0e-10:
                  first_3h_moisture[step] = current_moisture[output_indices]
      
              # 先写入题目60 s网格上的状态，再依据完整内部场判定终止。
              if step % output_stride == 0:
                  sampled_times.append(float(time_new_s))
                  sampled_moisture.append(current_moisture[output_indices].copy())
      
              current_max = float(np.max(current_moisture))
              if current_max < DRYING_THRESHOLD_KGKG:
                  # 严格小于阈值；前一整步状态和当前整场状态都保留供验收。
                  termination_time_s = float(time_new_s)
                  termination_state = current_moisture.copy()
                  termination_previous_state = previous_moisture.copy()
                  termination_previous_max = previous_max_moisture
                  termination_max = current_max
                  break
      
              if time_new_s % TABLE5_DT_S == 0.0:
                  table5_times.append(float(time_new_s))
                  table5_values.append(current_moisture[output_indices[KEY_RADIUS_INDICES]].copy())
      
              previous_max_moisture = current_max
              if progress and (step == 1 or step % int(TABLE5_DT_S / time_step_s) == 0):
                  print(
                      f"  已推进 {time_new_s / 3600.0:.1f} h，"
                      f"max C={current_max:.8f}，Picard={iterations}"
                  )
      
          if termination_time_s is None or termination_state is None:
              raise RuntimeError(
                  f"在{max_time_s / 3600.0:g} h内未达到全场严格阈值 "
                  f"max C < {DRYING_THRESHOLD_KGKG:g}"
              )
      
          return {
              "time_s": np.asarray(sampled_times, dtype=float),
              "radius_cm": OUTPUT_RADIUS_CM.copy(),
              "moisture_kgkg": np.asarray(sampled_moisture, dtype=float),
              "radii_m_internal": radii_m,
              "termination_time_s": termination_time_s,
              "termination_state_internal": termination_state,
              "termination_previous_state_internal": termination_previous_state,
              "termination_previous_max_kgkg": float(termination_previous_max),
              "termination_max_kgkg": float(termination_max),
              "first_3h_moisture_kgkg": first_3h_moisture,
              "iteration_counts": np.asarray(iteration_counts, dtype=int),
              "picard_delta_temperature": np.asarray(picard_delta_temperature, dtype=float),
              "picard_delta_moisture": np.asarray(picard_delta_moisture, dtype=float),
              "max_positive_step_change_kgkg": float(max_positive_step_change),
              "max_abs_step_change_kgkg": float(max_abs_step_change),
              "min_internal_moisture_kgkg": float(min_internal_moisture),
              "max_internal_moisture_kgkg": float(max_internal_moisture),
              "table5_times_s": np.asarray(table5_times, dtype=float),
              "table5_values_kgkg": np.asarray(table5_values, dtype=float)
              if table5_values
              else np.empty((0, KEY_RADIUS_INDICES.size), dtype=float),
          }
      
      
      def validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
          """执行问题三所需的最低限度数值、终止和结构检查。"""
      
          time_s = np.asarray(solution["time_s"], dtype=float)
          radius_cm = np.asarray(solution["radius_cm"], dtype=float)
          moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
          termination_state = np.asarray(solution["termination_state_internal"], dtype=float)
          previous_state = np.asarray(solution["termination_previous_state_internal"], dtype=float)
          if moisture.shape != (time_s.size, radius_cm.size):
              raise ValueError("问题三输出数组形状错误")
          if termination_state.shape != previous_state.shape:
              raise ValueError("终止前后内部场形状不一致")
          all_arrays = (time_s, radius_cm, moisture, termination_state, previous_state)
          if not all(np.all(np.isfinite(array)) for array in all_arrays):
              raise ValueError("问题三结果包含 NaN 或 Inf")
          if float(np.min(moisture)) < -1.0e-10 or float(np.min(termination_state)) < -1.0e-10:
              raise ValueError("问题三结果包含明显负水分浓度")
          if time_s.size < 1 or not np.isclose(time_s[0], 0.0, atol=1.0e-12):
              raise ValueError("输出时间未从0 s开始")
          if time_s.size > 1 and not np.allclose(np.diff(time_s), OUTPUT_DT_S, atol=1.0e-10):
              raise ValueError("输出时间间隔不是60 s")
          if radius_cm.size != 21 or not np.allclose(
              radius_cm, np.arange(0.0, 2.0000001, 0.1), atol=1.0e-12
          ):
              raise ValueError("输出半径不是0--2 cm、每0.1 cm")
      
          previous_max = float(solution["termination_previous_max_kgkg"])
          termination_max = float(solution["termination_max_kgkg"])
          if previous_max < DRYING_THRESHOLD_KGKG:
              raise ValueError("终止前一秒已低于阈值，终止记录不符合首次判定")
          if not termination_max < DRYING_THRESHOLD_KGKG:
              raise ValueError("终止时完整内部场未严格低于阈值")
          if not np.isclose(previous_max, float(np.max(previous_state)), atol=1.0e-12):
              raise ValueError("终止前最大水分浓度不是完整内部场最大值")
          if not np.isclose(termination_max, float(np.max(termination_state)), atol=1.0e-12):
              raise ValueError("终止时最大水分浓度不是完整内部场最大值")
      
          sampled_delta = np.diff(moisture, axis=0)
          max_positive_sampled_change = (
              float(np.max(sampled_delta)) if sampled_delta.size else 0.0
          )
          radial_delta = np.diff(moisture, axis=1)
          max_radial_increase = float(np.max(radial_delta)) if radial_delta.size else 0.0
          iterations = np.asarray(solution["iteration_counts"], dtype=int)

## Activity

    $ /bin/zsh -lc "sed -n '1,230p' problem/A题.md && printf '\\n--- task3 handoff gjs ---\\n' && sed -n '1,320p' handoff/task3_gjs_handoff.md && printf '\\n--- task3 handoff xby ---\\n' && sed -n '1,360p' handoff/task3_xby_handoff.md && printf '\\n--- task3 script remainder ---\\n' && sed -n '220,760p' solution/task3/script/solve_task3.py"
    status: Completed · exit 0
      # 2026 年高教社杯全国大学生数学建模竞赛题目
      
      > 请先阅读“全国大学生数学建模竞赛论文格式规范”
      
      # A 题 药材的烘干问题
      
      干燥是决定中药材成品品质的关键工序之一，其中热风烘干是一种常见的干燥方式。该方式主要包括预热平衡和恒温干燥两个阶段，通过调控烘房温湿环境，完成药材的干燥。在中药材烘干过程中，工艺参数选取不当容易导致干燥效率低、能耗高、成品品质不稳定等问题。而传统的试验优化模式存在成本高、周期长等问题，亟需借助数理分析与数值仿真的方法得到干燥规律。
      
      请建立数学模型解决以下问题。
      
      ## 问题 1
      
      某中药材形状大致呈圆柱形，长为 25 cm，半径为 2 cm。烘干开始时，药材的温度为 28°C，水分浓度（即干基含水率）为 2.55 kg/kg，烘房的温度（单位：°C）和水分浓度（单位：kg/kg）的变化情况见附件 1。
      
      请建立预热平衡阶段药材温度和水分浓度变化规律的数学模型（相关参数见附录 2），在论文中按表 1 和表 2 的格式分别给出 100、300、600、900、1200、1500、1800 s，到药材中心距离 0、0.5、1、1.5、2 cm 处的结果，并将 1800 s 内每隔 1 s、到药材中心距离每隔 0.1 cm 的完整结果保存到文件 `result1.xlsx` 中（模板文件见附件 3）。所有结果保留四位小数（下同）。
      
      ### 表 1 30 分钟内药材的温度
      
      | 时间/s | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |
      |---:|---:|---:|---:|---:|---:|
      | 100 |  |  |  |  |  |
      | 300 |  |  |  |  |  |
      | 600 |  |  |  |  |  |
      | 900 |  |  |  |  |  |
      | 1200 |  |  |  |  |  |
      | 1500 |  |  |  |  |  |
      | 1800 |  |  |  |  |  |
      
      > 表中各列表示“到药材中心的距离/cm”。
      
      ### 表 2 30 分钟内药材的水分浓度
      
      | 时间/s | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |
      |---:|---:|---:|---:|---:|---:|
      | 100 |  |  |  |  |  |
      | 300 |  |  |  |  |  |
      | 600 |  |  |  |  |  |
      | 900 |  |  |  |  |  |
      | 1200 |  |  |  |  |  |
      | 1500 |  |  |  |  |  |
      | 1800 |  |  |  |  |  |
      
      > 表中各列表示“到药材中心的距离/cm”。
      
      ## 问题 2
      
      烘干过程一般持续 2-3 天，预热平衡与恒温干燥阶段的参数有所不同。请建立整个烘干过程药材温度和水分浓度变化规律的数学模型（为简化问题，相关经验公式统一采用附录 3 中的公式），在论文中按表 3 和表 4 的格式分别给出 3 h 内每隔 0.5 h、到药材中心距离 0、0.5、1、1.5、2 cm 处的结果，并将每隔 1 s、到药材中心距离每隔 0.1 cm 的完整结果保存到文件 `result2.xlsx` 中（模板文件见附件 3）。
      
      ### 表 3 3 小时内药材的温度
      
      | 时间/h | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |
      |---:|---:|---:|---:|---:|---:|
      | 0.5 |  |  |  |  |  |
      | 1.0 |  |  |  |  |  |
      | 1.5 |  |  |  |  |  |
      | 2.0 |  |  |  |  |  |
      | 2.5 |  |  |  |  |  |
      | 3.0 |  |  |  |  |  |
      
      > 表中各列表示“到药材中心的距离/cm”。
      
      ### 表 4 3 小时内药材的水分浓度
      
      | 时间/h | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |
      |---:|---:|---:|---:|---:|---:|
      | 0.5 |  |  |  |  |  |
      | 1.0 |  |  |  |  |  |
      | 1.5 |  |  |  |  |  |
      | 2.0 |  |  |  |  |  |
      | 2.5 |  |  |  |  |  |
      | 3.0 |  |  |  |  |  |
      
      > 表中各列表示“到药材中心的距离/cm”。
      
      ## 问题 3
      
      按照烘干要求，药材各处的水分浓度应低于 0.15 kg/kg，请确定药材烘干所需要的时间（单位：h）。
      
      在论文中按表 5 的格式给出每隔 6 h、到药材中心距离每隔 0.5 cm 的水分浓度，并将药材内部水分浓度每隔 60 s、到药材中心距离每隔 0.1 cm 的完整结果保存到文件 `result3.xlsx` 中（模板文件见附件 3）。
      
      ### 表 5 药材烘干过程的水分浓度
      
      | 时间/h | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |
      |---:|---:|---:|---:|---:|---:|
      | 6 |  |  |  |  |  |
      | 12 |  |  |  |  |  |
      | 18 |  |  |  |  |  |
      | … |  |  |  |  |  |
      | 烘干结束时间 |  |  |  |  |  |
      
      > 表中各列表示“到药材中心的距离/cm”。
      
      ## 问题 4
      
      在实际烘干过程中，药材会因水分流失发生尺寸变化。请根据附件 2，确定药材的烘干时长（相关经验公式见附录 4）。
      
      在论文中按表 6 的格式给出每隔 6 h、到药材中心距离每隔 0.5 cm 的水分浓度，并将药材内部水分浓度每隔 60 s 时间、0.1 cm 距离的完整结果保存到文件 `result4.xlsx` 中（模板文件见附件 3）。
      
      ### 表 6 药材烘干过程的水分浓度
      
      | 时间/h | 0 cm | 0.5 cm | … | 药材表面 |
      |---:|---:|---:|---:|---:|
      | 6 |  |  |  |  |
      | 12 |  |  |  |  |
      | 18 |  |  |  |  |
      | … |  |  |  |  |
      | 烘干结束时间 |  |  |  |  |
      
      > 表中各列表示“到药材中心的距离/cm”。
      
      # 附录 1 附件说明
      
      附件 1 给出了烘干初期各时间点（单位：s）烘房的温度（单位：°C）和水分浓度（单位：kg/kg）。
      
      附件 2 给出了烘干过程中各时间点（单位：s）药材的半径（单位：cm）。
      
      附件 3 是结果文件夹，包括 4 个文件（`result1.xlsx`-`result4.xlsx`）。
      
      ## result1.xlsx 问题 1 的结果模板文件
      
      在“温度”和“水分浓度”工作表中分别保存问题 1 要求的温度（单位：°C）和水分浓度（单位：kg/kg），其中 A 列为时间（单位：s），第 1 行为到药材中心的距离（单位：cm）。
      
      ## result2.xlsx 问题 2 的结果模板文件
      
      在“温度”和“水分浓度”工作表中分别保存问题 2 要求的温度（单位：°C）和水分浓度（单位：kg/kg），其中 A 列为时间（单位：s），第 1 行为到药材中心的距离（单位：cm）。
      
      ## result3.xlsx 问题 3 的结果模板文件
      
      保存问题 3 要求的水分浓度（单位：kg/kg），其中 A 列为时间（单位：s），第 1 行为到药材中心的距离（单位：cm）。
      
      ## result4.xlsx 问题 4 的结果模板文件
      
      保存问题 4 要求的水分浓度（单位：kg/kg），其中 A 列为时间（单位：s），第 1 行为到药材中心的距离（单位：cm）。
      
      # 附录 2 问题 1 的相关参数
      
      密度为 820 kg/m³、比热容为 2600 J/(kg·K)、热传导系数为 0.36 W/(m·K)，对流换热系数为 25 W/(m²·K)，对流传质系数为 $8\times10^{-7}$ m/s。
      
      水分浓度扩散系数的经验公式为
      
      $$
      D = 7\times10^{-9}e^{-\frac{0.89}{C}}
      $$
      
      其中：
      
      - $D$ 为水分浓度扩散系数（单位：m²/s）；
      - $C$ 为药材水分浓度（单位：kg/kg）。
      
      # 附录 3 问题 2 和问题 3 的相关经验公式
      
      问题 2 和问题 3 用到的经验公式：
      
      $$
      \rho = 650 + 128C
      $$
      
      $$
      c_p = 1450 + 2736\cdot\frac{C}{C+1}
      $$
      
      $$
      k = 0.21 + 0.38\cdot\frac{C}{C+1}
      $$
      
      $$
      D = 2.4\times10^{-3}e^{-\frac{0.45}{C}}e^{-\frac{3850}{T}}
      $$
      
      其中：
      
      - $\rho$ 为密度（单位：kg/m³）；
      - $c_p$ 为比热容（单位：J/(kg·K)）；
      - $k$ 为热传导系数（单位：W/(m·K)）；
      - $D$ 为水分浓度扩散系数（单位：m²/s）；
      - $C$ 为药材水分浓度（单位：kg/kg）；
      - $T$ 为药材温度（单位：K）。
      
      # 附录 4 问题 4 的相关经验公式
      
      问题 4 用到的经验公式：
      
      $$
      \rho = 760 + 90C
      $$
      
      $$
      c_p = 1850 + 2150\cdot\frac{C}{C+1}
      $$
      
      $$
      k = 0.12 + 0.20\cdot\frac{C}{C+1}
      $$
      
      $$
      D = 4.2\times10^{-4}e^{-\frac{0.30}{C}}e^{-\frac{3850}{T}}
      $$
      
      其中：
      
      - $\rho$ 为密度（单位：kg/m³）；
      - $c_p$ 为比热容（单位：J/(kg·K)）；
      - $k$ 为热传导系数（单位：W/(m·K)）；
      - $D$ 为水分浓度扩散系数（单位：m²/s）；
      - $C$ 为药材水分浓度（单位：kg/kg）；
      - $T$ 为药材温度（单位：K）。
      
      --- task3 handoff gjs ---
      # A题第三问：药材烘干时间的确定与水分浓度计算结果
      
      ## 1. 问题分析
      
      问题3不需要重新建立新的温度方程和水分方程，而是在问题2的非线性温度—水分双向耦合模型基础上继续计算，直到药材内部所有位置的水分浓度都低于规定值
      
      \[
      C_{\mathrm{lim}}=0.15\ \mathrm{kg/kg}.
      \]
      
      相较于问题2，问题3新增了三项工作：
      
      1. 将附件1只给到4 h的烘房边界条件合理延拓到整个干燥过程；
      2. 将“药材各处水分浓度低于0.15”转化为数学停止条件；
      3. 精确定位第一次达到干燥要求的时刻，并按每6 h输出表5。
      
      ## 2. 沿用问题2的双向耦合模型
      
      ### 2.1 LaTeX源式
      
          \rho(C)c_p(C)\frac{\partial T}{\partial t}
          =\frac1r\frac{\partial}{\partial r}
          \left[rk(C)\frac{\partial T}{\partial r}\right],
      
          \frac{\partial C}{\partial t}
          =\frac1r\frac{\partial}{\partial r}
          \left[rD(T,C)\frac{\partial C}{\partial r}\right].
      
      ### 2.2 编译后的公式
      
      ![问题2的双向耦合控制方程](</Users/a1523647308/overleaf modify/A题第二问_assets/formula-1.png>)
      
      附录3的材料参数仍为：
      
      ### 2.3 LaTeX源式
      
          \rho(C)=650+128C,
      
          c_p(C)=1450+2736\frac{C}{C+1},
      
          k(C)=0.21+0.38\frac{C}{C+1},
      
          D(T,C)=2.4\times10^{-3}
          \exp\left(-\frac{0.45}{C}\right)
          \exp\left(-\frac{3850}{T+273.15}\right).
      
      ### 2.4 编译后的公式
      
      ![附录3经验公式](</Users/a1523647308/overleaf modify/A题第二问_assets/formula-2.png>)
      
      扩散系数公式中的温度使用开尔文，即
      
      \[
      T_K=T_{^\circ\mathrm C}+273.15.
      \]
      
      初始条件、中心对称条件以及表面对流换热、传质条件也与问题2相同：
      
      ![初始条件和边界条件](</Users/a1523647308/overleaf modify/A题第二问_assets/formula-3.png>)
      
      其中继续采用
      
      \[
      R=0.02\ \mathrm m,\qquad
      h=25\ \mathrm{W/(m^2\cdot K)},\qquad
      h_m=8\times10^{-7}\ \mathrm{m/s}.
      \]
      
      ## 3. 烘房边界条件的长期延拓
      
      附件1只记录到
      
      \[
      14400\ \mathrm s=4\ \mathrm h,
      \]
      
      而烘干过程持续两至三天，因此必须确定4 h以后的烘房环境。
      
      附件1在 \(9000\sim14400\ \mathrm s\) 内已经进入稳定阶段。对该时间段统计得到：
      
      | 变量 | 平均值 | 标准差 | 最小值 | 最大值 |
      |---|---:|---:|---:|---:|
      | 烘房温度/°C | 50.0049 | 0.1540 | 49.7570 | 50.2460 |
      | 烘房水分浓度/(kg/kg) | 0.049994 | 0.000153 | 0.049750 | 0.050250 |
      
      因此，前4 h使用附件1逐点分段线性插值，4 h后使用稳定段平均值。
      
      ### 3.1 LaTeX源式
      
          T_\infty(t)=
          \begin{cases}
          \widetilde T_\infty(t),&0\le t\le14400\ {\rm s},\\
          50.0049^\circ{\rm C},&t>14400\ {\rm s},
          \end{cases}
      
          C_\infty(t)=
          \begin{cases}
          \widetilde C_\infty(t),&0\le t\le14400\ {\rm s},\\
          0.049994\ {\rm kg/kg},&t>14400\ {\rm s}.
          \end{cases}
      
      ### 3.2 编译后的公式
      
      ![烘房边界条件延拓](</Users/a1523647308/overleaf modify/A题第三问_assets/formula-1.png>)
      
      采用稳定阶段平均值可以削弱测量噪声的影响，比直接使用最后一个观测值更稳健。
      
      ## 4. 烘干结束条件
      
      题目要求“药材各处的水分浓度应低于0.15 kg/kg”，因此停止条件应写成整个空间上的最大值条件。
      
      ### 4.1 LaTeX源式
      
          t_{\rm dry}=
          \inf\left\{t>0:
          \max_{0\le r\le R}C(r,t)\le0.15\right\}.
      
      由于干燥过程中水分由内部向表面迁移，始终有
      
          \frac{\partial C}{\partial r}\le0,
      
      从而
      
          \max_{0\le r\le R}C(r,t)=C(0,t).
      
      所以实际停止条件可化为
      
          C(0,t_{\rm dry})=0.15.
      
      ### 4.2 编译后的公式
      
      ![烘干结束条件](</Users/a1523647308/overleaf modify/A题第三问_assets/formula-2.png>)
      
      计算时仍然检查全部径向网格点。整个计算过程中没有出现水分空间顺序反转，数值结果始终满足
      
      \[
      C(0,t)\ge C(r,t)\ge C(R,t),
      \]
      
      因此中心确实是最后达到干燥标准的位置。
      
      ## 5. 数值求解过程
      
      ### 5.1 离散方法
      
      空间方向继续采用守恒型径向有限体积法，时间方向采用Crank–Nicolson格式。每个时间步使用Picard迭代同步更新
      
      \[
      \rho(C),\quad c_p(C),\quad k(C),\quad D(T,C).
      \]
      
      每个时间步的求解顺序如下：
      
      1. 根据当前水分浓度更新 \(\rho,c_p,k\)；
      2. 求解温度方程；
      3. 把温度转换为开尔文并更新 \(D(T,C)\)；
      4. 求解水分方程；
      5. 重复上述过程，直到温度和水分浓度同时收敛；
      6. 检查全部网格点是否满足 \(C\le0.15\)；
      7. 未满足则进入下一时间步，满足则定位结束时刻。
      
      最细网格计算中，每个时间步最多经过8次Picard迭代达到收敛。
      
      ### 5.2 分阶段时间步
      
      前4 h烘房环境变化较快，取
      
      \[
      \Delta t=2\ \mathrm s.
      \]
      
      4 h后烘房进入稳定阶段，温湿度和水分场变化明显变慢，取
      
      \[
      \Delta t=10\ \mathrm s.
      \]
      
      为了验证时间步误差，另用前4 h为1 s、4 h后为5 s进行复算，得到的结束时刻仅相差
      
      \[
      0.0073\ \mathrm s,
      \]
      
      说明时间离散误差可以忽略。
      
      ### 5.3 阈值时刻定位
      
      若相邻两个时间层满足
      
      \[
      C(0,t_n)>0.15,\qquad C(0,t_{n+1})<0.15,
      \]
      
      则在线性时间插值下定位结束时刻。
      
      #### LaTeX源式
      
          t_{\rm dry}\approx t_n+
          \frac{C(0,t_n)-0.15}
          {C(0,t_n)-C(0,t_{n+1})}
          (t_{n+1}-t_n).
      
      #### 编译后的公式
      
      ![结束时刻插值公式](</Users/a1523647308/overleaf modify/A题第三问_assets/formula-3.png>)
      
      ## 6. 空间网格收敛检验
      
      干燥后期含水率下降使 \(D(T,C)\) 显著减小，药材表面附近形成较陡的水分梯度。因此，问题3所需空间网格应比问题2更细。
      
      | 径向区间数 \(N\) | \(\Delta r\)/cm | 计算得到的结束时间/h | 相对上一网格变化/h |
      |---:|---:|---:|---:|
      | 200 | 0.01000 | 58.9449 | — |
      | 400 | 0.00500 | 57.6779 | 1.2671 |
      | 800 | 0.00250 | 57.5031 | 0.1748 |
      | 1600 | 0.00125 | 57.4719 | 0.0312 |
      
      可以看到，网格持续加密后结束时刻逐渐稳定。最终结果采用 \(N=1600\) 的最细网格。最后两级网格的差为0.0312 h，约1.87 min，可视为当前离散下的保守数值不确定度。
      
      ## 7. 烘干结束时间
      
      最细网格计算得到
      
      \[
      \boxed{
      t_{\mathrm{dry}}=57.4719\ \mathrm h
      }
      \]
      
      即约为
      
      \[
      2\ \mathrm d\ 9\ \mathrm h\ 28\ \mathrm{min}.
      \]
      
      实用工艺上可向上取整为
      
      \[
      \boxed{57.5\ \mathrm h}
      \]
      
      以保证药材中心不会高于规定水分浓度。
      
      ## 8. 表5：药材烘干过程的水分浓度
      
      单位：kg/kg。
      
      | 时间/h | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |
      |---:|---:|---:|---:|---:|---:|
      | 6 | 1.0169 | 0.9881 | 0.9015 | 0.7550 | 0.5328 |
      | 12 | 0.4561 | 0.4431 | 0.4030 | 0.3297 | 0.1642 |
      | 18 | 0.2988 | 0.2915 | 0.2687 | 0.2253 | 0.0845 |
      | 24 | 0.2378 | 0.2327 | 0.2167 | 0.1855 | 0.0665 |
      | 30 | 0.2058 | 0.2018 | 0.1892 | 0.1641 | 0.0598 |
      | 36 | 0.1859 | 0.1825 | 0.1718 | 0.1504 | 0.0566 |
      | 42 | 0.1721 | 0.1691 | 0.1597 | 0.1407 | 0.0548 |
      | 48 | 0.1618 | 0.1592 | 0.1507 | 0.1334 | 0.0537 |
      | 54 | 0.1539 | 0.1514 | 0.1436 | 0.1277 | 0.0530 |
      | 烘干结束：57.4719 | 0.1500 | 0.1477 | 0.1402 | 0.1249 | 0.0527 |
      
      烘干结束时药材温度已经基本均匀，各指定位置的温度均约为
      
      \[
      50.0049^\circ\mathrm C.
      \]
      
      ## 9. 结果分析
      
      ### 9.1 中心位置决定烘干结束时间
      
      在全部输出时刻，水分浓度均由中心向表面递减。57.4719 h时中心水分浓度恰好达到0.1500 kg/kg，而其他位置均已低于标准，因此该时刻就是整根药材满足要求的最早时刻。
      
      如果只根据药材表面判断，在12 h左右表面水分浓度就已经接近0.15，但此时中心仍为0.4561，会严重低估烘干时间。
      
      ### 9.2 干燥速度先快后慢
      
      前12 h内中心水分浓度由2.55下降到0.4561，下降较快；之后从0.4561下降到0.15却又需要约45.47 h。
      
      这是附录3扩散系数中
      
      \[
      \exp\left(-\frac{0.45}{C}\right)
      \]
      
      造成的。当 \(C\) 下降时，该指数项迅速减小，使有效扩散系数下降，形成明显的降速干燥阶段。
      
      ### 9.3 表面水分浓度接近环境值
      
      烘干结束时表面水分浓度为0.0527 kg/kg，已非常接近恒温阶段的环境水分浓度0.0500 kg/kg。中心仍为0.1500，说明末期的主要限制来自药材内部水分扩散，而不是表面对流传质。
      
      ## 10. 稳定边界的敏感性分析
      
      以附件1稳定阶段的最小值和最大值构造两个边界情景：
      
      | 情景 | 温度/°C | 环境水分浓度/(kg/kg) | 对烘干时间的作用 |
      |---|---:|---:|---|
      | 较快干燥 | 50.2460 | 0.049750 | 相对基准约缩短0.358 h |
      | 基准 | 50.0049 | 0.049994 | 57.4719 h |
      | 较慢干燥 | 49.7570 | 0.050250 | 相对基准约延长0.378 h |
      
      据此估计，附件稳定段的小幅波动对应的结束时间范围约为
      
      \[
      \boxed{
      57.11\ \mathrm h\le t_{\mathrm{dry}}\le57.85\ \mathrm h
      }.
      \]
      
      这说明模型给出的57.47 h对正常烘房波动具有较好的稳定性。实际工艺若需要更保守的设定，可以采用58 h。
      
      ## 11. 合理性检验
      
      1. 全程没有出现负水分浓度或数值振荡；
      2. 全程满足中心水分浓度最高、表面水分浓度最低；
      3. 药材温度最终收敛到稳定烘房温度；
      4. 药材表面水分浓度最终接近环境水分浓度；
      5. 烘干时间约为2.39 d，处于题目所述通常持续2至3 d的范围内；
      6. 时间步减半后结束时刻几乎不变，空间网格加密后结果逐渐收敛。
      
      ## 12. 可直接写入论文的结论
      
      --- task3 handoff xby ---
      # Codex conversation
      
      ## User
      
      你现在负责 2026CUMCM 项目的 A 题问题三真实求解。你的唯一目标是得到可信的最终数值答案，并实际生成题目要求的结果文件。不要停留在讨论、方案建议或论文写作阶段。
      
      【一、你的身份与工作方式】
      
      你是 5.6-sol medium，作为整个任务的根模型。
      
      你的职责仅限于：
      1. 理解我的要求和题目；
      2. 阅读现有问题一、问题二的模型、代码和结果；
      3. 决定问题三应该怎样继承问题二；
      4. 给 luna-worker 下达明确、范围有限的任务；
      5. 审查 luna-worker 的实现和数值结果；
      6. 判断结果是否合理，发现问题后继续派 luna-worker 修正；
      7. 最终汇总真实求解结果。
      
      代码编写、修改 Python、运行求解器、生成 CSV/XLSX、数值实验、调试等实际执行工作，应主动派给 luna-worker 完成。
      
      不要自己大段写实现代码。
      不要为了显得复杂而建立大量 agent。
      原则上一个执行中的 luna-worker 完成一个明确任务即可，需要修改时继续派 worker 处理。
      
      除非遇到真正无法自动解决的阻塞问题，否则不要频繁询问我，也不要每一步等待确认。
      
      【二、项目目录】
      
      当前项目根目录为：
      
      2026CUMCM
      ├── context
      │   └── context-task1-1_xby.md
      ├── handoff
      │   ├── task1_gjs_handoff.md
      │   └── task1_xby_handoff.md
      ├── problem
      │   ├── A题.md
      │   ├── A题.pdf
      │   └── 附件
      │       ├── 附件1.xlsx
      │       ├── 附件2.xlsx
      │       └── 附件3
      │           ├── result1.xlsx
      │           ├── result2.xlsx
      │           ├── result3.xlsx
      │           └── result4.xlsx
      └── solution
          └── task1
              ├── answer
              │   ├── task1_key_results.csv
              │   └── task1_result.csv
              └── script
                  └── solve_task1.py
      
      开始后先执行 pwd、git status，并检查仓库当前真实目录结构。
      
      尤其要主动搜索仓库里是否已经存在：
      - solution/task2/
      - task2 求解脚本
      - task2 的 answer/
      - task2 的 context/handoff
      - task2 的最新 Git 提交
      
      我给出的目录可能不是此刻仓库的完整最新状态，以实际 Git 工作区为准。
      
      【三、开始前必须阅读的内容】
      
      首先阅读：
      
      1. problem/A题.md
      2. 与问题二有关的最新 context / handoff，如果仓库中存在
      3. solution/task2 中的问题二求解代码和结果，如果存在
      4. 必要时参考 solution/task1，但不要重新求问题一
      
      附件本身没有问题。
      
      不要浪费时间检查附件是否合法、是否损坏、格式是否规范、是否存在版权问题。
      不要对附件做所谓的防御性验证。
      直接把题目和附件作为可信输入使用。
      
      尤其禁止修改 problem/ 下的任何原始文件。
      
      【四、问题三的数学任务】
      
      问题三要求：
      
      药材各处水分浓度均低于
      
      C < 0.15 kg/kg
      
      时认为烘干完成。
      
      需要确定药材烘干所需要的时间，单位为 h。
      
      问题三继续采用问题二和问题三统一规定的附录 3 经验公式：
      
      ρ = 650 + 128C
      
      cp = 1450 + 2736 * C/(C+1)
      
      k = 0.21 + 0.38 * C/(C+1)
      
      D = 2.4×10^-3 * exp(-0.45/C) * exp(-3850/T)
      
      其中 T 必须使用 K。
      
      问题三不是重新建立一套独立模型。
      
      必须优先直接继承问题二已经确定的：
      - 温度控制方程
      - 水分扩散方程
      - 圆柱径向一维模型
      - 初始条件
      - 表面对流换热条件
      - 表面对流传质条件
      - 烘房温度和水分浓度随时间的处理
      - 预热阶段与恒温干燥阶段衔接方式
      - 空间离散方法
      - 时间积分方法
      - 非线性参数更新方式
      
      问题三的本质是在问题二求解器基础上，把模拟时间继续向后延长，直到满足终止条件。
      
      不得因为进入问题三就重新选择一套不同的 PDE、边界条件或数值算法。
      
      如果当前仓库中存在多个问题二版本，以最新、已经实际运行并输出最终问题二结果的版本作为基线，同时结合 Git 历史确认。
      
      【五、终止条件】
      
      真正的烘干结束条件是：
      
      max_r C(r,t) < 0.15 kg/kg
      
      也就是整个药材内部所有计算位置都已经低于 0.15。
      
      不要仅仅检查表面。
      不要仅仅因为平均含水率低于 0.15 就停止。
      
      虽然理论上中心通常可能是最后达到要求的位置，但程序仍应直接检查完整径向水分场，不要把“中心一定最后干”硬编码成终止条件。
      
      从 t=0 开始延续问题二模型进行求解，不要把问题三错误地当成“从第 3 h 重新开始一个新问题”。
      
      可以复用问题二在前 3 h 已经计算得到的状态或直接一次性积分完整时间区间，两种实现只要数学上连续一致即可。
      
      【六、需要生成的文件】
      
      新建：
      
      solution/task3/
      ├── script/
      │   └── solve_task3.py
      └── answer/
          ├── result3.xlsx
          └── task3_all_results.csv
      
      原则上只需要一个 solve_task3.py。
      不要为了这个任务建立大型框架。
      
      1. result3.xlsx
      
      必须以：
      
      problem/附件/附件3/result3.xlsx
      
      为模板。
      
      禁止覆盖原模板。
      
      复制模板结构后写入：
      
      solution/task3/answer/result3.xlsx
      
      按照 A题.md 的要求：
      
      - 保存药材内部水分浓度
      - A 列为时间，单位 s
      - 第一行为到药材中心距离，单位 cm
      - 时间间隔为 60 s
      - 距离间隔为 0.1 cm
      - 半径范围 0～2 cm
      - 一直保存到烘干结束附近
      - 所有结果保留四位小数
      
      如果最终烘干时刻不是 60 s 的整数倍：
      完整结果文件仍按照题目规定的 60 s 间隔保存；
      最终烘干时间另外准确报告，不要为了让时间落在 60 s 网格上人为改变终止条件。
      
      2. task3_all_results.csv
      
      生成：
      
      solution/task3/answer/task3_all_results.csv
      
      CSV 要包含问题三完整答案，至少采用清晰的长表结构：
      
      time_s,radius_cm,moisture_kgkg
      
      要求：
      - t 从 0 到烘干结束
      - 输出时间间隔 60 s
      - radius_cm = 0,0.1,0.2,...,2.0
      - 数值保留四位小数
      
      CSV 与 result3.xlsx 中对应位置的数据必须一致。
      
      【七、论文表 5 所需结果】
      
      除了完整结果，还必须实际提取题目表 5 所需的数据。
      
      时间：
      
      6 h
      12 h
      18 h
      24 h
      30 h
      ……
      
      每隔 6 h 一行，一直列到烘干结束前。
      
      空间位置：
      
      0 cm
      0.5 cm
      1.0 cm
      1.5 cm
      2.0 cm
      
      最后额外给出：
      
      “烘干结束时间”
      
      这一行对应上述 5 个位置的水分浓度。
      
      最终汇报中直接打印出完整的表 5 数值，使我可以直接拿去写论文。
      
      所有数值保留四位小数。
      
      同时明确报告：
      
      烘干结束时间 = ____ h
      
      不要只说“大约两天”或给一个时间范围。
      
      【八、数值求解原则】
      
      核心原则是继承问题二，而不是重新调参。
      
      如果问题二已经使用固定的：
      - Δr
      - 时间步
      - Crank–Nicolson
      - BDF
      - Picard
      - 算术平均或调和平均
      - 插值方式
      
      问题三全部保持一致，除非长时间积分出现明确的数值错误。
      
      不得为了让结果更“漂亮”而改变参数。
      
      如果问题二已经验证过数值方案，则问题三不要重新进行大规模收敛性研究。
      
      只做最低限度的合理性检查：
      
      1. 是否出现 NaN / Inf；
      2. 水分浓度是否总体随时间下降；
      3. 是否出现明显非物理负值或严重振荡；
      4. t=0～3 h 的问题三结果是否与问题二对应结果一致；
      5. 终止时刻之前是否仍至少有某处 C >= 0.15；
      6. 终止时刻是否已经所有位置 C < 0.15；
      7. CSV 与 XLSX 对应数据是否一致。
      
      这几项够用，不要扩展成测试工程。
      
      【九、严禁过度工程化】
      
      这是数学建模竞赛真实求解任务，目标是尽快得到合理、可解释、可写进论文的最终答案。
      
      严禁：
      
      - 建大型类体系
      - 建插件系统
      - 做复杂 CLI
      - 写 YAML 配置系统
      - Docker
      - CI/CD
      - 数据库
      - Web 页面
      - 大量单元测试
      - 为 task4 提前设计抽象接口
      - 全面重构 task1/task2
      - 为极端不可能输入设计大量异常处理
      - 讨论版权
      - 检查附件是否可信
      - 对不存在的异常输入做防御式编程
      - 擅自加入 CFD
      - 擅自改成二维或三维模型
      - 神经网络
      - 黑箱优化
      - 为了“模型更真实”擅自增加题目没有要求的复杂物理机制
      
      只实现解决问题三所需的东西。
      
      发现一个小问题时优先直接修复，不要借机重构整个工程。
      
      【十、Git 版本管理是硬要求】
      
      整个过程必须做好 Git 版本管理。
      
      开始前先：
      
      git status
      git log --oneline -n 10
      
      不得破坏已有 task1/task2 结果。
      
      每形成一个有意义、可以运行的版本，都必须 commit。
      
      所有 commit message 必须使用中文。
      
      例如：
      
      git commit -m "新增问题三长期烘干求解器"
      git commit -m "实现烘干终止时间判定"
      git commit -m "生成问题三完整结果文件"
      git commit -m "修正问题三结果输出并完成验证"
      
      具体 message 根据实际修改填写，不能机械照抄。
      
      禁止英文 commit message。
      
      不要把所有工作堆到最后只提交一次。
      
      同时也不要为了刷 commit 数量制造无意义的小提交。
      
      标准是：每个真实可识别的工作版本都应有对应 commit。
      
      最终必须保证：
      
      git status
      
      没有遗漏的、应该提交的 task3 修改。
      
      不要擅自 push，除非我明确要求。
      
      【十一、执行流程】
      
      按下面顺序直接执行：
      
      第一阶段：
      5.6-sol medium 阅读题目、Git 状态、问题二上下文、问题二代码和结果，明确问题三继承的数学模型。
      
      第二阶段：
      根模型给 luna-worker 明确任务，在 solution/task3/script/solve_task3.py 中基于 task2 求解器实现长时间积分和 C<0.15 的终止判定。
      
      实际运行。
      
      
      --- task3 script remainder ---
          time_s = np.asarray(solution["time_s"], dtype=float)
          radius_cm = np.asarray(solution["radius_cm"], dtype=float)
          moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
          termination_state = np.asarray(solution["termination_state_internal"], dtype=float)
          previous_state = np.asarray(solution["termination_previous_state_internal"], dtype=float)
          if moisture.shape != (time_s.size, radius_cm.size):
              raise ValueError("问题三输出数组形状错误")
          if termination_state.shape != previous_state.shape:
              raise ValueError("终止前后内部场形状不一致")
          all_arrays = (time_s, radius_cm, moisture, termination_state, previous_state)
          if not all(np.all(np.isfinite(array)) for array in all_arrays):
              raise ValueError("问题三结果包含 NaN 或 Inf")
          if float(np.min(moisture)) < -1.0e-10 or float(np.min(termination_state)) < -1.0e-10:
              raise ValueError("问题三结果包含明显负水分浓度")
          if time_s.size < 1 or not np.isclose(time_s[0], 0.0, atol=1.0e-12):
              raise ValueError("输出时间未从0 s开始")
          if time_s.size > 1 and not np.allclose(np.diff(time_s), OUTPUT_DT_S, atol=1.0e-10):
              raise ValueError("输出时间间隔不是60 s")
          if radius_cm.size != 21 or not np.allclose(
              radius_cm, np.arange(0.0, 2.0000001, 0.1), atol=1.0e-12
          ):
              raise ValueError("输出半径不是0--2 cm、每0.1 cm")
      
          previous_max = float(solution["termination_previous_max_kgkg"])
          termination_max = float(solution["termination_max_kgkg"])
          if previous_max < DRYING_THRESHOLD_KGKG:
              raise ValueError("终止前一秒已低于阈值，终止记录不符合首次判定")
          if not termination_max < DRYING_THRESHOLD_KGKG:
              raise ValueError("终止时完整内部场未严格低于阈值")
          if not np.isclose(previous_max, float(np.max(previous_state)), atol=1.0e-12):
              raise ValueError("终止前最大水分浓度不是完整内部场最大值")
          if not np.isclose(termination_max, float(np.max(termination_state)), atol=1.0e-12):
              raise ValueError("终止时最大水分浓度不是完整内部场最大值")
      
          sampled_delta = np.diff(moisture, axis=0)
          max_positive_sampled_change = (
              float(np.max(sampled_delta)) if sampled_delta.size else 0.0
          )
          radial_delta = np.diff(moisture, axis=1)
          max_radial_increase = float(np.max(radial_delta)) if radial_delta.size else 0.0
          iterations = np.asarray(solution["iteration_counts"], dtype=int)
          if iterations.size == 0 or np.max(iterations) > PICARD_MAX_ITER:
              raise ValueError("Picard迭代记录为空或超出上限")
      
          return {
              "termination_time_s": float(solution["termination_time_s"]),
              "termination_time_h": float(solution["termination_time_s"]) / 3600.0,
              "termination_previous_max_kgkg": previous_max,
              "termination_max_kgkg": termination_max,
              "max_positive_step_change_kgkg": float(
                  solution["max_positive_step_change_kgkg"]
              ),
              "max_positive_sampled_change_kgkg": max_positive_sampled_change,
              "max_abs_step_change_kgkg": float(solution["max_abs_step_change_kgkg"]),
              "max_radial_increase_kgkg": max_radial_increase,
              "min_internal_moisture_kgkg": float(solution["min_internal_moisture_kgkg"]),
              "max_internal_moisture_kgkg": float(solution["max_internal_moisture_kgkg"]),
              "max_picard_iterations": int(np.max(iterations)),
              "mean_picard_iterations": float(np.mean(iterations)),
              "sample_count": int(time_s.size),
              "internal_node_count": int(termination_state.size),
          }
      
      
      def compare_with_task2(
          solution: dict[str, Any], task2_csv_path: str | Path = DEFAULT_TASK2_CSV_PATH
      ) -> dict[str, float | int]:
          """比较问题三在0--3 h的1 s输出与问题二最终CSV。"""
      
          first_3h = np.asarray(solution["first_3h_moisture_kgkg"], dtype=float)
          if not np.all(np.isfinite(first_3h)):
              raise ValueError("问题三未完整记录0--3 h场，无法与问题二比较")
          frame = pd.read_csv(Path(task2_csv_path))
          required_columns = {"time_s", "radius_cm", "moisture_kgkg"}
          if not required_columns.issubset(frame.columns):
              raise ValueError("问题二CSV缺少比较所需列")
          expected_rows = 10801 * 21
          if len(frame) != expected_rows:
              raise ValueError(f"问题二CSV记录数为{len(frame)}，不是{expected_rows}")
          task2_moisture = frame["moisture_kgkg"].to_numpy(dtype=float).reshape((10801, 21))
          raw_difference = np.abs(first_3h - task2_moisture)
          rounded_difference = np.abs(np.round(first_3h, 4) - np.round(task2_moisture, 4))
          return {
              "rows_compared": expected_rows,
              "max_abs_difference_raw_kgkg": float(np.max(raw_difference)),
              "max_abs_difference_4dp_kgkg": float(np.max(rounded_difference)),
          }
      
      
      def write_result_xlsx(
          solution: dict[str, Any],
          output_path: str | Path = DEFAULT_XLSX_PATH,
          template_path: str | Path = DEFAULT_TEMPLATE_PATH,
      ) -> None:
          """复制问题三模板结构并写入60 s采样水分场。"""
      
          output_path = Path(output_path)
          output_path.parent.mkdir(parents=True, exist_ok=True)
          workbook = load_workbook(Path(template_path))
          if workbook.sheetnames != ["Sheet1"]:
              raise ValueError(f"问题三模板工作表不符合要求: {workbook.sheetnames}")
          worksheet = workbook["Sheet1"]
          time_s = np.asarray(solution["time_s"], dtype=float)
          radius_cm = np.asarray(solution["radius_cm"], dtype=float)
          moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
          if time_s.size != moisture.shape[0] or radius_cm.size != moisture.shape[1]:
              raise ValueError("xlsx写入数组形状错误")
      
          header_style = copy(worksheet.cell(row=1, column=2)._style)
          time_style = copy(worksheet.cell(row=2, column=1)._style)
          value_style = copy(worksheet.cell(row=2, column=2)._style)
          if worksheet.max_row > 1:
              worksheet.delete_rows(2, worksheet.max_row - 1)
          for column_index, radius in enumerate(radius_cm, start=2):
              cell = worksheet.cell(row=1, column=column_index, value=round(float(radius), 1))
              cell._style = copy(header_style)
              cell.number_format = "0.0"
          for row_index, time_value in enumerate(time_s, start=2):
              time_cell = worksheet.cell(row=row_index, column=1, value=int(round(time_value)))
              time_cell._style = copy(time_style)
              time_cell.number_format = "0"
              for column_index, value in enumerate(moisture[row_index - 2], start=2):
                  cell = worksheet.cell(
                      row=row_index,
                      column=column_index,
                      value=float(f"{float(value):.4f}"),
                  )
                  cell._style = copy(value_style)
                  cell.number_format = "0.0000"
          workbook.save(output_path)
      
      
      def write_result_csv(
          solution: dict[str, Any], output_path: str | Path = DEFAULT_CSV_PATH
      ) -> None:
          """写入问题三要求的long-format三列CSV。"""
      
          output_path = Path(output_path)
          output_path.parent.mkdir(parents=True, exist_ok=True)
          time_s = np.asarray(solution["time_s"], dtype=float)
          radius_cm = np.asarray(solution["radius_cm"], dtype=float)
          moisture = np.asarray(solution["moisture_kgkg"], dtype=float)
          with output_path.open("w", newline="", encoding="utf-8") as stream:
              writer = csv.writer(stream)
              writer.writerow(["time_s", "radius_cm", "moisture_kgkg"])
              for time_index, time_value in enumerate(time_s):
                  for radius_index, radius_value in enumerate(radius_cm):
                      writer.writerow(
                          [
                              int(round(time_value)),
                              f"{radius_value:.1f}",
                              f"{moisture[time_index, radius_index]:.4f}",
                          ]
                      )
      
      
      def validate_written_outputs(
          solution: dict[str, Any],
          xlsx_path: str | Path = DEFAULT_XLSX_PATH,
          csv_path: str | Path = DEFAULT_CSV_PATH,
      ) -> dict[str, Any]:
          """读取答案文件并检查结构及CSV/XLSX四位小数一致性。"""
      
          expected = np.round(np.asarray(solution["moisture_kgkg"], dtype=float), 4)
          expected_times = np.asarray(solution["time_s"], dtype=int)
          expected_radius = np.asarray(solution["radius_cm"], dtype=float)
      
          frame = pd.read_csv(Path(csv_path))
          if list(frame.columns) != ["time_s", "radius_cm", "moisture_kgkg"]:
              raise ValueError(f"问题三CSV字段不符合要求: {list(frame.columns)}")
          expected_rows = expected_times.size * expected_radius.size
          if len(frame) != expected_rows:
              raise ValueError(f"问题三CSV行数为{len(frame)}，不是{expected_rows}")
          csv_times = frame["time_s"].to_numpy(dtype=int)
          csv_radius = frame["radius_cm"].to_numpy(dtype=float)
          csv_values = frame["moisture_kgkg"].to_numpy(dtype=float).reshape(expected.shape)
          if not np.array_equal(csv_times, np.repeat(expected_times, expected_radius.size)):
              raise ValueError("问题三CSV时间结构错误")
          if not np.allclose(csv_radius, np.tile(expected_radius, expected_times.size), atol=1.0e-12):
              raise ValueError("问题三CSV半径结构错误")
      
          workbook = load_workbook(Path(xlsx_path), read_only=True, data_only=True)
          if workbook.sheetnames != ["Sheet1"]:
              raise ValueError(f"问题三答案工作表错误: {workbook.sheetnames}")
          worksheet = workbook["Sheet1"]
          if worksheet.max_row != expected_times.size + 1 or worksheet.max_column != expected_radius.size + 1:
              raise ValueError("问题三答案xlsx尺寸错误")
          # ReadOnlyWorksheet.cell() restarts the XML parser for every cell.  Consume
          # the worksheet once by rows so validation remains fast for the long file.
          rows = list(
              worksheet.iter_rows(
                  min_row=1,
                  max_row=worksheet.max_row,
                  min_col=1,
                  max_col=worksheet.max_column,
                  values_only=True,
              )
          )
          xlsx_times = np.asarray([row[0] for row in rows[1:]], dtype=int)
          xlsx_radius = np.asarray(rows[0][1:], dtype=float)
          xlsx_values = np.asarray([row[1:] for row in rows[1:]], dtype=float)
          if not np.array_equal(xlsx_times, expected_times) or not np.allclose(
              xlsx_radius, expected_radius, atol=1.0e-12
          ):
              raise ValueError("问题三答案xlsx时间或半径结构错误")
          xlsx_values = np.round(xlsx_values, 4)
          if not np.array_equal(csv_values, xlsx_values):
              raise ValueError("问题三CSV与xlsx对应水分值不一致")
          if not np.array_equal(csv_values, expected):
              raise ValueError("问题三答案文件与求解器采样值不一致")
          return {
              "rows": int(expected_rows),
              "xlsx_shape": (int(worksheet.max_row), int(worksheet.max_column)),
              "max_abs_csv_xlsx_difference_kgkg": float(np.max(np.abs(csv_values - xlsx_values))),
          }
      
      
      def _print_table5(solution: dict[str, Any]) -> None:
          """打印每6 h采样和精确终止状态对应的表5。"""
      
          regular_times = np.asarray(solution["table5_times_s"], dtype=float)
          regular_values = np.asarray(solution["table5_values_kgkg"], dtype=float)
          termination_time = float(solution["termination_time_s"])
          termination_state = np.asarray(solution["termination_state_internal"], dtype=float)
          termination_values = termination_state[
              task2._output_indices(np.asarray(solution["radii_m_internal"], dtype=float))[KEY_RADIUS_INDICES]
          ]
          print("表5 水分浓度 / kg/kg（列为0、0.5、1.0、1.5、2.0 cm）")
          print("时间/h,0 cm,0.5 cm,1.0 cm,1.5 cm,2.0 cm")
          for time_value, row in zip(regular_times, regular_values):
              print(
                  f"{time_value / 3600.0:.1f},"
                  + ",".join(f"{float(value):.4f}" for value in row)
              )
          print(
              f"烘干结束时间 ({termination_time / 3600.0:.6f} h),"
              + ",".join(f"{float(value):.4f}" for value in termination_values)
          )
      
      
      def main() -> None:
          parser = argparse.ArgumentParser(description="求解A题问题三")
          parser.add_argument("--max-time", type=float, default=DEFAULT_MAX_TIME_S)
          parser.add_argument("--time-step", type=float, default=TIME_STEP_S)
          parser.add_argument("--output-dt", type=float, default=OUTPUT_DT_S)
          parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH)
          parser.add_argument("--task2-csv", type=Path, default=DEFAULT_TASK2_CSV_PATH)
          parser.add_argument("--no-write", action="store_true", help="只求解和验证，不写答案文件")
          args = parser.parse_args()
      
          started = wall_time.perf_counter()
          print(
              f"问题三求解开始: dt={args.time_step:g}s, output_dt={args.output_dt:g}s, "
              f"dr={BASE_DR_M:g}m, threshold C<{DRYING_THRESHOLD_KGKG:g}"
          )
          solution = solve_task3(
              data_path=args.data_path,
              max_time_s=args.max_time,
              time_step_s=args.time_step,
              output_dt_s=args.output_dt,
              progress=True,
          )
          summary = validate_solution(solution)
          comparison = compare_with_task2(solution, args.task2_csv)
          print(f"基本数值检查: {summary}")
          print(f"0--3 h与问题二CSV全量比较: {comparison}")
          if not args.no_write:
              write_result_xlsx(solution)
              write_result_csv(solution)
              output_check = validate_written_outputs(solution)
              print(f"答案文件检查: {output_check}")
              print(f"已生成: {DEFAULT_XLSX_PATH}")
              print(f"已生成: {DEFAULT_CSV_PATH}")
          _print_table5(solution)
          print(f"烘干结束时间 = {summary['termination_time_h']:.6f} h")
          print(f"总耗时: {wall_time.perf_counter() - started:.2f} s")
      
      
      if __name__ == "__main__":
          main()

## Activity

    $ /bin/zsh -lc "git log --oneline -n 12 && printf '\\n--- task3 constants/imports ---\\n' && sed -n '1,220p' solution/task3/script/solve_task3.py && printf '\\n--- task2 constants ---\\n' && sed -n '1,180p' solution/task2/script/solve_task2.py && printf '\\n--- task3 recent handoff tail ---\\n' && tail -260 handoff/task3_xby_handoff.md && printf '\\n--- task2 recent handoff tail ---\\n' && tail -220 handoff/task2_xby_handoff.md"
    status: Completed · exit 0
      735fbbd 生成问题三完整结果文件并通过验证
      b5a750c 优化问题三答案文件验证读取
      1f53b08 新增问题三长期烘干求解器
      e3f08be 修正问题二交接文档时间离散表述
      f90d788 补充问题二数值模型交接文档
      ed97452 修正问题二烘房边界数据
      94ffe31 修正问题二结果模板格式
      f423a75 统一问题一结果文件格式
      9375a01 生成问题二最终结果并完成数值验证
      e1db607 完成问题二三小时热质耦合求解
      a520f6d 完成问题二动态物性求解框架
      c87b74d 补充问题一交接资料并清理系统文件
      
      --- task3 constants/imports ---
      """A题问题三：继承问题二模型的长期烘干求解器。
      
      问题三从 t=0 连续推进问题二的固定半径、动态物性热质耦合模型，
      在每个 dt=1 s 的内部时间步检查完整径向水分场，首次满足
      max_r C(r,t) < 0.15 kg/kg 时停止。输出文件只保留题目要求的
      60 s 时间网格；精确终止时刻和终止状态用于表5及验证报告。
      """
      
      from __future__ import annotations
      
      import argparse
      import csv
      import sys
      import time as wall_time
      from copy import copy
      from pathlib import Path
      from typing import Any
      
      import numpy as np
      import pandas as pd
      from openpyxl import load_workbook
      
      
      # 直接复用问题二的数值核心和模型常量，不改变问题二算法。
      TASK2_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "task2" / "script"
      if str(TASK2_SCRIPT_DIR) not in sys.path:
          sys.path.insert(0, str(TASK2_SCRIPT_DIR))
      import solve_task2 as task2  # noqa: E402
      
      
      RADIUS_M = task2.RADIUS_M
      BASE_DR_M = task2.BASE_DR_M
      INITIAL_TEMPERATURE_C = task2.INITIAL_TEMPERATURE_C
      INITIAL_MOISTURE_KGKG = task2.INITIAL_MOISTURE_KGKG
      HEAT_TRANSFER_W_M2_K = task2.HEAT_TRANSFER_W_M2_K
      MASS_TRANSFER_M_S = task2.MASS_TRANSFER_M_S
      PICARD_MAX_ITER = task2.PICARD_MAX_ITER
      OUTPUT_RADIUS_CM = task2.OUTPUT_RADIUS_CM.copy()
      
      TIME_STEP_S = 1.0
      OUTPUT_DT_S = 60.0
      TABLE5_DT_S = 6.0 * 3600.0
      DRYING_THRESHOLD_KGKG = 0.15
      # 题目说明过程一般持续2--3天；上限仅用于防止异常情况下无限循环。
      DEFAULT_MAX_TIME_S = 7.0 * 24.0 * 3600.0
      
      REPO_ROOT = Path(__file__).resolve().parents[3]
      DEFAULT_DATA_PATH = REPO_ROOT / "problem" / "附件" / "附件1.xlsx"
      DEFAULT_TEMPLATE_PATH = REPO_ROOT / "problem" / "附件" / "附件3" / "result3.xlsx"
      DEFAULT_XLSX_PATH = Path(__file__).resolve().parents[1] / "answer" / "result3.xlsx"
      DEFAULT_CSV_PATH = (
          Path(__file__).resolve().parents[1] / "answer" / "task3_all_results.csv"
      )
      DEFAULT_TASK2_CSV_PATH = (
          REPO_ROOT / "solution" / "task2" / "answer" / "task2_all_results.csv"
      )
      
      KEY_RADIUS_INDICES = np.array([0, 5, 10, 15, 20], dtype=int)
      
      
      def _output_indices(radii_m: np.ndarray) -> np.ndarray:
          """取得题目要求的0--2 cm、每0.1 cm输出位置。"""
      
          target_m = OUTPUT_RADIUS_CM / 100.0
          indices = np.array([int(np.argmin(np.abs(radii_m - r))) for r in target_m])
          if not np.allclose(radii_m[indices], target_m, atol=1.0e-12, rtol=0.0):
              raise ValueError("当前内部网格不能精确包含题目要求的0.1 cm输出位置")
          return indices
      
      
      def solve_task3(
          data_path: str | Path = DEFAULT_DATA_PATH,
          max_time_s: float = DEFAULT_MAX_TIME_S,
          time_step_s: float = TIME_STEP_S,
          output_dt_s: float = OUTPUT_DT_S,
          dr_m: float = BASE_DR_M,
          progress: bool = False,
      ) -> dict[str, Any]:
          """从 t=0 连续推进问题二状态，直到完整场严格低于阈值。"""
      
          if max_time_s <= 0.0 or time_step_s <= 0.0 or output_dt_s <= 0.0:
              raise ValueError("时间上限、时间步和输出间隔必须为正")
          max_steps_float = max_time_s / time_step_s
          max_steps = int(np.floor(max_steps_float + 1.0e-10))
          if max_steps < 1 or not np.isclose(max_steps_float, max_steps, atol=1.0e-10):
              raise ValueError("时间上限必须由整数个内部时间步组成")
          output_ratio = output_dt_s / time_step_s
          output_stride = int(round(output_ratio))
          if not np.isclose(output_ratio, output_stride, atol=1.0e-10):
              raise ValueError("输出间隔必须是内部时间步的整数倍")
      
          # 附件1只覆盖初期，np.interp 在末点以后按题目要求保持最后边界值。
          air_time_s, air_temperature, air_moisture = task2.load_air_data(
              data_path, required_end_s=0.0
          )
          air_temperature_interp = lambda t: float(np.interp(t, air_time_s, air_temperature))
          air_moisture_interp = lambda t: float(np.interp(t, air_time_s, air_moisture))
      
          radii_m, faces_m, radial_measure_m2 = task2.control_volume_geometry(RADIUS_M, dr_m)
          output_indices = _output_indices(radii_m)
          n_nodes = radii_m.size
      
          current_temperature = np.full(n_nodes, INITIAL_TEMPERATURE_C, dtype=float)
          current_moisture = np.full(n_nodes, INITIAL_MOISTURE_KGKG, dtype=float)
      
          sampled_times: list[float] = [0.0]
          sampled_moisture: list[np.ndarray] = [current_moisture[output_indices].copy()]
          first_3h_moisture = np.full((10801, output_indices.size), np.nan, dtype=float)
          first_3h_moisture[0] = current_moisture[output_indices]
          table5_times: list[float] = []
          table5_values: list[np.ndarray] = []
      
          iteration_counts: list[int] = []
          picard_delta_temperature: list[float] = []
          picard_delta_moisture: list[float] = []
          max_positive_step_change = -np.inf
          max_abs_step_change = 0.0
          min_internal_moisture = float(np.min(current_moisture))
          max_internal_moisture = float(np.max(current_moisture))
          previous_max_moisture = float(np.max(current_moisture))
          termination_time_s: float | None = None
          termination_state: np.ndarray | None = None
          termination_previous_state: np.ndarray | None = None
          termination_previous_max = np.nan
          termination_max = np.nan
      
          for step in range(1, max_steps + 1):
              time_new_s = step * time_step_s
              previous_moisture = current_moisture
              (
                  current_temperature,
                  current_moisture,
                  iterations,
                  delta_temperature,
                  delta_moisture,
              ) = task2._picard_step(
                  current_temperature,
                  previous_moisture,
                  time_new_s,
                  time_step_s,
                  radial_measure_m2,
                  faces_m,
                  dr_m,
                  air_temperature_interp(time_new_s),
                  air_moisture_interp(time_new_s),
              )
              iteration_counts.append(int(iterations))
              picard_delta_temperature.append(float(delta_temperature))
              picard_delta_moisture.append(float(delta_moisture))
      
              change = current_moisture - previous_moisture
              max_positive_step_change = max(max_positive_step_change, float(np.max(change)))
              max_abs_step_change = max(max_abs_step_change, float(np.max(np.abs(change))))
              min_internal_moisture = min(min_internal_moisture, float(np.min(current_moisture)))
              max_internal_moisture = max(max_internal_moisture, float(np.max(current_moisture)))
      
              if time_new_s <= 10800.0 + 1.0e-10:
                  first_3h_moisture[step] = current_moisture[output_indices]
      
              # 先写入题目60 s网格上的状态，再依据完整内部场判定终止。
              if step % output_stride == 0:
                  sampled_times.append(float(time_new_s))
                  sampled_moisture.append(current_moisture[output_indices].copy())
      
              current_max = float(np.max(current_moisture))
              if current_max < DRYING_THRESHOLD_KGKG:
                  # 严格小于阈值；前一整步状态和当前整场状态都保留供验收。
                  termination_time_s = float(time_new_s)
                  termination_state = current_moisture.copy()
                  termination_previous_state = previous_moisture.copy()
                  termination_previous_max = previous_max_moisture
                  termination_max = current_max
                  break
      
              if time_new_s % TABLE5_DT_S == 0.0:
                  table5_times.append(float(time_new_s))
                  table5_values.append(current_moisture[output_indices[KEY_RADIUS_INDICES]].copy())
      
              previous_max_moisture = current_max
              if progress and (step == 1 or step % int(TABLE5_DT_S / time_step_s) == 0):
                  print(
                      f"  已推进 {time_new_s / 3600.0:.1f} h，"
                      f"max C={current_max:.8f}，Picard={iterations}"
                  )
      
          if termination_time_s is None or termination_state is None:
              raise RuntimeError(
                  f"在{max_time_s / 3600.0:g} h内未达到全场严格阈值 "
                  f"max C < {DRYING_THRESHOLD_KGKG:g}"
              )
      
          return {
              "time_s": np.asarray(sampled_times, dtype=float),
              "radius_cm": OUTPUT_RADIUS_CM.copy(),
              "moisture_kgkg": np.asarray(sampled_moisture, dtype=float),
              "radii_m_internal": radii_m,
              "termination_time_s": termination_time_s,
              "termination_state_internal": termination_state,
              "termination_previous_state_internal": termination_previous_state,
              "termination_previous_max_kgkg": float(termination_previous_max),
              "termination_max_kgkg": float(termination_max),
              "first_3h_moisture_kgkg": first_3h_moisture,
              "iteration_counts": np.asarray(iteration_counts, dtype=int),
              "picard_delta_temperature": np.asarray(picard_delta_temperature, dtype=float),
              "picard_delta_moisture": np.asarray(picard_delta_moisture, dtype=float),
              "max_positive_step_change_kgkg": float(max_positive_step_change),
              "max_abs_step_change_kgkg": float(max_abs_step_change),
              "min_internal_moisture_kgkg": float(min_internal_moisture),
              "max_internal_moisture_kgkg": float(max_internal_moisture),
              "table5_times_s": np.asarray(table5_times, dtype=float),
              "table5_values_kgkg": np.asarray(table5_values, dtype=float)
              if table5_values
              else np.empty((0, KEY_RADIUS_INDICES.size), dtype=float),
          }
      
      
      def validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
          """执行问题三所需的最低限度数值、终止和结构检查。"""
      
          time_s = np.asarray(solution["time_s"], dtype=float)
      
      --- task2 constants ---
      """A题问题二：动态物性圆柱径向热质耦合求解。
      
      模型沿用问题一的圆柱径向守恒有限体积离散，时间方向使用后向欧拉。
      问题二的 rho、cp、k、D 在每个时间步的 Picard 迭代中由当前 T、C 更新，
      从而得到当前时间步内的自洽隐式解。内部网格含 r=0 和 r=R 两个节点，
      两端为半控制体积；输出网格为每 1 s、每 0.1 cm。
      """
      
      from __future__ import annotations
      
      import argparse
      import csv
      import time as wall_time
      from copy import copy
      from pathlib import Path
      from typing import Any
      
      import numpy as np
      import pandas as pd
      from openpyxl import load_workbook
      from scipy.linalg import solve_banded
      
      
      # 几何、初始状态和输出约定（内部长度统一使用 m）。
      RADIUS_M = 0.02
      LENGTH_M = 0.25  # 一维径向守恒式中约去，保留作题目参数记录。
      BASE_DR_M = 0.000125
      INITIAL_TEMPERATURE_C = 28.0
      INITIAL_MOISTURE_KGKG = 2.55
      FINAL_TIME_S = 10800.0
      OUTPUT_DT_S = 1.0
      OUTPUT_RADIUS_CM = np.arange(0.0, 2.0000001, 0.1)
      
      # 问题一沿用的边界传递参数。
      HEAT_TRANSFER_W_M2_K = 25.0
      MASS_TRANSFER_M_S = 8.0e-7
      
      # Picard 收敛参数。绝对阈值足以保证四位小数输出稳定，同时避免无意义地
      # 将迭代压到机器精度。
      PICARD_TOL_T_C = 1.0e-8
      PICARD_TOL_C_KGKG = 1.0e-10
      PICARD_MAX_ITER = 50
      
      DEFAULT_DATA_PATH = (
          Path(__file__).resolve().parents[3] / "problem" / "附件" / "附件1.xlsx"
      )
      DEFAULT_TEMPLATE_PATH = (
          Path(__file__).resolve().parents[3]
          / "problem"
          / "附件"
          / "附件3"
          / "result2.xlsx"
      )
      DEFAULT_XLSX_PATH = Path(__file__).resolve().parents[1] / "answer" / "result2.xlsx"
      DEFAULT_CSV_PATH = (
          Path(__file__).resolve().parents[1] / "answer" / "task2_all_results.csv"
      )
      
      
      def load_air_data(
          path: str | Path = DEFAULT_DATA_PATH,
          required_end_s: float = FINAL_TIME_S,
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
          """读取附件1的全部烘房边界数据，供求解区间内分段线性插值。"""
      
          frame = pd.read_excel(Path(path))
          column_map = {str(column).strip(): column for column in frame.columns}
          required = ("时间", "温度", "水分浓度")
          missing = [column for column in required if column not in column_map]
          if missing:
              raise ValueError(f"附件1缺少必需列: {missing}; 实际列为 {list(frame.columns)!r}")
      
          selected = frame[[column_map[column] for column in required]].copy()
          selected.columns = required
          for column in required:
              selected[column] = pd.to_numeric(selected[column], errors="raise")
          selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")
      
          time_s = selected["时间"].to_numpy(dtype=float)
          air_temperature_C = selected["温度"].to_numpy(dtype=float)
          air_moisture_kgkg = selected["水分浓度"].to_numpy(dtype=float)
          if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
              raise ValueError("附件1时间必须包含至少两个严格递增时间点")
          if time_s[0] > 1.0e-10 or time_s[-1] < required_end_s - 1.0e-10:
              raise ValueError(f"附件1烘房边界数据未覆盖 0--{required_end_s:g} s")
          if not np.all(np.isfinite(np.column_stack((time_s, air_temperature_C, air_moisture_kgkg)))):
              raise ValueError("附件1烘房边界数据包含非有限数值")
          return time_s, air_temperature_C, air_moisture_kgkg
      
      
      def control_volume_geometry(
          radius_m: float = RADIUS_M, dr_m: float = BASE_DR_M
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
          """返回含两端半控制体积的节点、面和径向测度。"""
      
          if radius_m <= 0.0 or dr_m <= 0.0:
              raise ValueError("半径和空间步长必须为正")
          n_intervals = int(round(radius_m / dr_m))
          if not np.isclose(n_intervals * dr_m, radius_m, rtol=0.0, atol=1.0e-12):
              raise ValueError("当前网格要求半径可由整数个 dr 划分")
          radii_m = np.linspace(0.0, radius_m, n_intervals + 1)
          faces_m = 0.5 * (radii_m[:-1] + radii_m[1:])
          radial_measure_m2 = np.empty_like(radii_m)
          radial_measure_m2[0] = 0.5 * faces_m[0] ** 2
          radial_measure_m2[1:-1] = 0.5 * (faces_m[1:] ** 2 - faces_m[:-1] ** 2)
          radial_measure_m2[-1] = 0.5 * (radius_m**2 - faces_m[-1] ** 2)
          return radii_m, faces_m, radial_measure_m2
      
      
      def material_properties(
          temperature_C: np.ndarray, moisture_kgkg: np.ndarray
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
          """按当前 Picard 状态计算 rho、cp、k 和 D（SI 单位）。"""
      
          temperature_C = np.asarray(temperature_C, dtype=float)
          moisture_kgkg = np.asarray(moisture_kgkg, dtype=float)
          concentration = np.maximum(moisture_kgkg, 1.0e-12)
          temperature_K = temperature_C + 273.15
          if np.any(temperature_K <= 0.0):
              raise ValueError("动态物性计算遇到非正 Kelvin 温度")
      
          rho = 650.0 + 128.0 * concentration
          cp = 1450.0 + 2736.0 * concentration / (concentration + 1.0)
          k = 0.21 + 0.38 * concentration / (concentration + 1.0)
          diffusivity = 2.4e-3 * np.exp(-0.45 / concentration) * np.exp(
              -3850.0 / temperature_K
          )
          return rho, cp, k, diffusivity
      
      
      def _solve_tridiagonal(
          lower: np.ndarray, diagonal: np.ndarray, upper: np.ndarray, rhs: np.ndarray
      ) -> np.ndarray:
          """解三对角线性系统，矩阵系数均为当前 Picard 冻结值。"""
      
          n = diagonal.size
          banded = np.zeros((3, n), dtype=float)
          banded[0, 1:] = upper
          banded[1, :] = diagonal
          banded[2, :-1] = lower
          return solve_banded((1, 1), banded, rhs, check_finite=False)
      
      
      def _solve_temperature_linear(
          old_temperature_C: np.ndarray,
          guess_temperature_C: np.ndarray,
          guess_moisture_kgkg: np.ndarray,
          radial_measure_m2: np.ndarray,
          faces_m: np.ndarray,
          dr_m: float,
          dt_s: float,
          air_temperature_C: float,
      ) -> np.ndarray:
          """在给定 Picard 物性下求解一个后向欧拉温度步。"""
      
          rho, cp, conductivity, _ = material_properties(
              guess_temperature_C, guess_moisture_kgkg
          )
          storage = rho * cp * radial_measure_m2
          face_k = 0.5 * (conductivity[:-1] + conductivity[1:])
          conductance = face_k * faces_m / dr_m
      
          diagonal = storage.copy()
          diagonal[0] += dt_s * conductance[0]
          diagonal[1:-1] += dt_s * (conductance[:-1] + conductance[1:])
          diagonal[-1] += dt_s * (
              conductance[-1] + RADIUS_M * HEAT_TRANSFER_W_M2_K
          )
          lower = -dt_s * conductance.copy()
          upper = -dt_s * conductance.copy()
          rhs = storage * old_temperature_C
          rhs[-1] += dt_s * RADIUS_M * HEAT_TRANSFER_W_M2_K * air_temperature_C
          return _solve_tridiagonal(lower, diagonal, upper, rhs)
      
      
      def _solve_moisture_linear(
          old_moisture_kgkg: np.ndarray,
          guess_temperature_C: np.ndarray,
          guess_moisture_kgkg: np.ndarray,
          radial_measure_m2: np.ndarray,
      
      --- task3 recent handoff tail ---
                 worksheet = workbook["Sheet1"]
                 if worksheet.max_row != expected_times.size + 1 or worksheet.max_column != expected_radius.size + 1:
                     raise ValueError("问题三答案xlsx尺寸错误")
            -    xlsx_times = np.asarray(
            -        [worksheet.cell(row=row, column=1).value for row in range(2, worksheet.max_row + 1)],
            -        dtype=int,
            -    )
            -    xlsx_radius = np.asarray(
            -        [worksheet.cell(row=1, column=column).value for column in range(2, worksheet.max_column + 1)],
            -        dtype=float,
            -    )
            -    xlsx_values = np.asarray(
            -        [
            -            [worksheet.cell(row=row, column=column).value for column in range(2, worksheet.max_column + 1)]
            -            for row in range(2, worksheet.max_row + 1)
            -        ],
            -        dtype=float,
            +    # ReadOnlyWorksheet.cell() restarts the XML parser for every cell.  Consume
            +    # the worksheet once by rows so validation remains fast for the long file.
            +    rows = list(
            +        worksheet.iter_rows(
            +            min_row=1,
            +            max_row=worksheet.max_row,
            +            min_col=1,
            +            max_col=worksheet.max_column,
            +            values_only=True,
            +        )
                 )
            +    xlsx_times = np.asarray([row[0] for row in rows[1:]], dtype=int)
            +    xlsx_radius = np.asarray(rows[0][1:], dtype=float)
            +    xlsx_values = np.asarray([row[1:] for row in rows[1:]], dtype=float)
                 if not np.array_equal(xlsx_times, expected_times) or not np.allclose(
                     xlsx_radius, expected_radius, atol=1.0e-12
                 ):
      
      ## Activity
      
          $ /bin/zsh -lc 'git show --stat --oneline 1f53b08 && git show --stat --oneline b5a750c && git show --stat --oneline 735fbbd'
          status: Completed · exit 0
            1f53b08 新增问题三长期烘干求解器
             solution/task3/script/solve_task3.py | 500 +++++++++++++++++++++++++++++++++++
             1 file changed, 500 insertions(+)
            b5a750c 优化问题三答案文件验证读取
             solution/task3/script/solve_task3.py | 27 +++++++++++++--------------
             1 file changed, 13 insertions(+), 14 deletions(-)
            735fbbd 生成问题三完整结果文件并通过验证
             solution/task3/answer/result3.xlsx          |   Bin 0 -> 350563 bytes
             solution/task3/answer/task3_all_results.csv | 71947 ++++++++++++++++++++++++++
             2 files changed, 71947 insertions(+)
      
      ## Activity
      
          $ /bin/zsh -lc "git status --short --branch && git log --format='%h %s' -8 && git diff --check && git diff --name-only -- problem solution/task1 solution/task2 && git diff --cached --name-status"
          status: Completed · exit 0
            ## main...origin/main [ahead 6]
            A  context/context-task2-1_xby.md
            A  handoff/task2_gjs_handoff.md
            ?? .DS_Store
            ?? handoff/task2_handoff.md
            ?? solution/.DS_Store
            ?? solution/task2/.DS_Store
            ?? solution/task2/script/__pycache__/
            735fbbd 生成问题三完整结果文件并通过验证
            b5a750c 优化问题三答案文件验证读取
            1f53b08 新增问题三长期烘干求解器
            e3f08be 修正问题二交接文档时间离散表述
            f90d788 补充问题二数值模型交接文档
            ed97452 修正问题二烘房边界数据
            94ffe31 修正问题二结果模板格式
            f423a75 统一问题一结果文件格式
            A	context/context-task2-1_xby.md
            A	handoff/task2_gjs_handoff.md
      
      ## Assistant
      
      静态审查未发现终止判定偷换：程序每 `1 s` 对 161 个内部节点直接取 `max(C)`，并保留前一秒与当前完整场；task3 直接调用 task2 的单步矩阵和 Picard 核心，因此 0–3 h 算法路径一致。接下来做两项新鲜证据：独立读取比较已生成 CSV/XLSX，以及以 `--no-write` 重新跑完整求解确认 `205515 s` 可复现。
      
      ## Activity
      
          $ /bin/zsh -lc '/Users/jiaqiaosu/miniconda3/bin/python solution/task3/script/solve_task3.py --no-write'
          status: Completed · exit 0
            问题三求解开始: dt=1s, output_dt=60s, dr=0.000125m, threshold C<0.15
              已推进 0.0 h，max C=2.55000000，Picard=4
              已推进 6.0 h，max C=1.01557809，Picard=4
              已推进 12.0 h，max C=0.45477545，Picard=4
              已推进 18.0 h，max C=0.29789504，Picard=4
              已推进 24.0 h，max C=0.23707588，Picard=3
              已推进 30.0 h，max C=0.20521475，Picard=3
              已推进 36.0 h，max C=0.18533894，Picard=3
              已推进 42.0 h，max C=0.17157676，Picard=3
              已推进 48.0 h，max C=0.16137591，Picard=3
              已推进 54.0 h，max C=0.15344580，Picard=3
            基本数值检查: {'termination_time_s': 205515.0, 'termination_time_h': 57.0875, 'termination_previous_max_kgkg': 0.15000008550654267, 'termination_max_kgkg': 0.14999979160076163, 'max_positive_step_change_kgkg': 1.3322676295501878e-15, 'max_positive_sampled_change_kgkg': 2.6645352591003757e-15, 'max_abs_step_change_kgkg': 0.020603324222667307, 'max_radial_increase_kgkg': 3.1086244689504383e-15, 'min_internal_moisture_kgkg': 0.05253468708885245, 'max_internal_moisture_kgkg': 2.550000000000005, 'max_picard_iterations': 4, 'mean_picard_iterations': 3.308921489915578, 'sample_count': 3426, 'internal_node_count': 161}
            0--3 h与问题二CSV全量比较: {'rows_compared': 226821, 'max_abs_difference_raw_kgkg': 4.999974650510275e-05, 'max_abs_difference_4dp_kgkg': 0.0}
            表5 水分浓度 / kg/kg（列为0、0.5、1.0、1.5、2.0 cm）
            时间/h,0 cm,0.5 cm,1.0 cm,1.5 cm,2.0 cm
            6.0,1.0156,0.9869,0.9006,0.7547,0.5335
            12.0,0.4548,0.4419,0.4020,0.3289,0.1640
            18.0,0.2979,0.2906,0.2679,0.2247,0.0843
            24.0,0.2371,0.2320,0.2161,0.1850,0.0663
            30.0,0.2052,0.2012,0.1886,0.1636,0.0597
            36.0,0.1853,0.1820,0.1713,0.1499,0.0565
            42.0,0.1716,0.1686,0.1592,0.1402,0.0547
            48.0,0.1614,0.1587,0.1503,0.1330,0.0536
            54.0,0.1534,0.1510,0.1432,0.1273,0.0528
            烘干结束时间 (57.087500 h),0.1500,0.1477,0.1402,0.1248,0.0525
            烘干结束时间 = 57.087500 h
            总耗时: 35.58 s
      
      ## Activity
      
          $ /bin/zsh -lc "git status --short --branch && git diff --check && git diff --exit-code -- solution/task3 problem/附件/附件3/result3.xlsx && git ls-files solution/task3 | sort && git log --format='%H %s' -3"
          status: Completed · exit 0
            ## main...origin/main [ahead 6]
            A  context/context-task2-1_xby.md
            A  handoff/task2_gjs_handoff.md
            ?? .DS_Store
            ?? handoff/task2_handoff.md
            ?? solution/.DS_Store
            ?? solution/task2/.DS_Store
            ?? solution/task2/script/__pycache__/
            solution/task3/answer/result3.xlsx
            solution/task3/answer/task3_all_results.csv
            solution/task3/script/solve_task3.py
            735fbbd3af64999ab7beea3662c85c6c7d4b71c7 生成问题三完整结果文件并通过验证
            b5a750c4e89b3897c641d1b68455a8d79bb84581 优化问题三答案文件验证读取
            1f53b08f49c9a8c460993ad36aa2b8e1960ae28a 新增问题三长期烘干求解器
      
      ## Activity
      
          $ /bin/zsh -lc "/Users/jiaqiaosu/miniconda3/bin/python - <<'PY'from openpyxl import load_workbookfor p in ['problem/附件/附件3/result3.xlsx','solution/task3/answer/result3.xlsx']: w=load_workbook(p, read_only=False, data_only=True); s=w.active print(p, w.sheetnames, s.max_row, s.max_column, s['A1'].value, s['B1'].value, s['A2'].value, s['B2'].value, s['B2'].number_format)PY"
          status: Completed · exit 0
            problem/附件/附件3/result3.xlsx ['Sheet1'] 5 6 时间\到药材中心的距离 0 60 None General
            solution/task3/answer/result3.xlsx ['Sheet1'] 3427 22 时间\到药材中心的距离 0 0 2.55 0.0000
      
      ## Activity
      
          $ /bin/zsh -lc "/Users/jiaqiaosu/miniconda3/bin/python - <<'PY'import csv, reimport numpy as npimport pandas as pdfrom openpyxl import load_workbookcsv_path='solution/task3/answer/task3_all_results.csv'xlsx_path='solution/task3/answer/result3.xlsx'with open(csv_path, newline='', encoding='utf-8') as f:    reader=csv.DictReader(f)    raw=list(reader)assert reader.fieldnames == ['time_s','radius_cm','moisture_kgkg']assert all(re.fullmatch(r'-?\\d+\\.\\d{4}', r['moisture_kgkg']) for r in raw)df=pd.DataFrame(raw)times=df.time_s.astype(int).to_numpy()radii=df.radius_cm.astype(float).to_numpy()vals=df.moisture_kgkg.astype(float).to_numpy()ut=np.unique(times)ur=np.unique(radii)matrix=vals.reshape(len(ut),len(ur))wb=load_workbook(xlsx_path, read_only=True, data_only=True)ws=wb['Sheet1']rows=list(ws.iter_rows(values_only=True))xt=np.array([r[0] for r in rows[1:]], dtype=int)xr=np.array(rows[0][1:], dtype=float)xv=np.array([r[1:] for r in rows[1:]], dtype=float)print('csv_rows',len(raw),'shape',matrix.shape)print('times',ut[0],ut[-1],'count',len(ut),'unique_step',np.unique(np.diff(ut)).tolist())print('radii',ur[0],ur[-1],'count',len(ur),'unique_step',np.unique(np.round(np.diff(ur),10)).tolist())print('finite',np.isfinite(matrix).all(),'min',matrix.min(),'max',matrix.max())print('max_temporal_increase_rounded',np.diff(matrix,axis=0).max())print('xlsx_shape',ws.max_row,ws.max_column,'sheetnames',wb.sheetnames)print('xlsx_csv_max_abs',np.max(np.abs(xv-matrix)))print('xlsx_time_equal',np.array_equal(xt,ut),'xlsx_radius_equal',np.array_equal(xr,ur))print('last_csv_center_surface',matrix[-1,0],matrix[-1,-1])print('last_time_center_max',matrix[-1].max())PY"
          status: Completed · exit 0
            csv_rows 71946 shape (3426, 21)
            times 0 205500 count 3426 unique_step [60]
            radii 0.0 2.0 count 21 unique_step [0.1]
            finite True min 0.0525 max 2.55
            max_temporal_increase_rounded 0.0
            xlsx_shape 3427 22 sheetnames ['Sheet1']
            xlsx_csv_max_abs 0.0
            xlsx_time_equal True xlsx_radius_equal True
            last_csv_center_surface 0.15 0.0525
            last_time_center_max 0.15
      
      ## Assistant
      
      验收结果：候选终止时间已由根模型全量 `--no-write` 重跑复现，耗时 `35.58 s`，仍为 `205515 s`；结束前一秒全场最大值 `0.1500000855`，结束时 `0.1499997916`。独立读取 71,946 条 CSV 记录并逐点对照 XLSX，最大差为 0；task3 已全部提交。现在只整理最终高价值结果。
      
      ## Activity
      
          $ /bin/zsh -lc "/Users/jiaqiaosu/miniconda3/bin/python - <<'PY'import pandas as pdf=pd.read_excel('problem/附件/附件1.xlsx')print(f.tail(3).to_string(index=False))PY"
          status: Completed · exit 0
               时间     温度    水分浓度
            14280 49.759 0.04996
            14340 49.805 0.04995
            14400 50.165 0.04986
      
      ## Assistant
      
      烘干结束时间 = **57.087500 h**，即 **205515 s**。这是首次满足完整径向场 `max_r C(r,t) < 0.15 kg/kg` 的时刻。
      
      ## 表 5：药材烘干过程水分浓度
      
      单位：kg/kg，保留四位小数。
      
      | 时间/h | 0 cm | 0.5 cm | 1.0 cm | 1.5 cm | 2.0 cm |
      |---:|---:|---:|---:|---:|---:|
      | 6 | 1.0156 | 0.9869 | 0.9006 | 0.7547 | 0.5335 |
      | 12 | 0.4548 | 0.4419 | 0.4020 | 0.3289 | 0.1640 |
      | 18 | 0.2979 | 0.2906 | 0.2679 | 0.2247 | 0.0843 |
      | 24 | 0.2371 | 0.2320 | 0.2161 | 0.1850 | 0.0663 |
      | 30 | 0.2052 | 0.2012 | 0.1886 | 0.1636 | 0.0597 |
      | 36 | 0.1853 | 0.1820 | 0.1713 | 0.1499 | 0.0565 |
      | 42 | 0.1716 | 0.1686 | 0.1592 | 0.1402 | 0.0547 |
      | 48 | 0.1614 | 0.1587 | 0.1503 | 0.1330 | 0.0536 |
      | 54 | 0.1534 | 0.1510 | 0.1432 | 0.1273 | 0.0528 |
      | 烘干结束时间（57.087500 h） | 0.1500 | 0.1477 | 0.1402 | 0.1248 | 0.0525 |
      
      结束行中心值显示为 `0.1500` 是四位小数舍入结果；未舍入值严格小于 `0.15`。
      
      ## 已生成文件
      
      - [solve_task3.py](/Users/jiaqiaosu/Desktop/作业/2026夏季学期/2026CUMCM/2026CUMCM/solution/task3/script/solve_task3.py)
      - [result3.xlsx](/Users/jiaqiaosu/Desktop/作业/2026夏季学期/2026CUMCM/2026CUMCM/solution/task3/answer/result3.xlsx)
      - [task3_all_results.csv](/Users/jiaqiaosu/Desktop/作业/2026夏季学期/2026CUMCM/2026CUMCM/solution/task3/answer/task3_all_results.csv)
      
      结果文件包含 `3426` 个时间点、`21` 个径向位置，共 `71946` 条记录；时间为 `0–205500 s`、间隔 `60 s`。精确结束时间 `205515 s` 单独报告。
      
      ## 继承的问题二方法
      
      - 固定圆柱半径：`R=0.02 m`
      - 径向一维有限体积法：`dr=0.000125 m`，共 `161` 个内部节点
      - 后向欧拉：`dt=1 s`
      - 界面 `k`、`D` 使用算术平均
      - 每个时间步使用 Picard 迭代更新 `ρ(C)、cp(C)、k(C)、D(T,C)`
      - Picard 最大迭代次数：实际 `4` 次
      - 对流换热系数：`h=25 W/(m²·K)`
      - 对流传质系数：`h_m=8×10⁻⁷ m/s`
      - 附件1数据内采用分段线性插值；`14400 s` 后保持末值 `50.165°C、0.04986 kg/kg`
      - 从 `t=0` 连续积分，没有从第 3 h 重新初始化
      
      ## 验证结果
      
      - 结束前一秒（`205514 s`）全场最大水分浓度：`0.1500000855`
      - 结束时（`205515 s`）全场最大水分浓度：`0.1499997916`
      - 无 NaN、Inf 或负水分浓度
      - 最大单步正向变化仅 `1.33×10⁻¹⁵ kg/kg`，未发现明显振荡
      - 0–3 h 与问题二共 `226821` 个时间—半径点在四位小数下完全一致
      - 与问题二已舍入 CSV 的原始最大差：`4.99997×10⁻⁵ kg/kg`
      - CSV 与 XLSX 全部对应值最大差：`0`
      - 根模型重新执行完整 `--no-write` 求解，复现终止时间 `205515 s`
      
      ## Git 提交
      
      - `1f53b08f49c9a8c460993ad36aa2b8e1960ae28a` — 新增问题三长期烘干求解器
      - `b5a750c4e89b3897c641d1b68455a8d79bb84581` — 优化问题三答案文件验证读取
      - `735fbbd3af64999ab7beea3662c85c6c7d4b71c7` — 生成问题三完整结果文件并通过验证
      
      最终 `git status`：
      
      ```text
      ## main...origin/main [ahead 6]
      A  context/context-task2-1_xby.md
      A  handoff/task2_gjs_handoff.md
      ?? .DS_Store
      ?? handoff/task2_handoff.md
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/
      ```
      
      `solution/task3/` 没有未提交修改。上述状态均为非 task3 的既有或并发文件，未混入本次提交。
      
      ## Activity
      
          $ /bin/zsh -lc 'git status'
          status: Completed · exit 0
            On branch main
            Your branch is ahead of 'origin/main' by 6 commits.
              (use "git push" to publish your local commits)
      
            Changes to be committed:
              (use "git restore --staged <file>..." to unstage)
            	new file:   context/context-task2-1_xby.md
            	new file:   handoff/task2_gjs_handoff.md
      
            Untracked files:
              (use "git add <file>..." to include in what will be committed)
            	.DS_Store
            	handoff/task2_handoff.md
            	solution/.DS_Store
            	solution/task2/.DS_Store
            	solution/task2/script/__pycache__/
      
      
      --- task2 recent handoff tail ---
      T_K=T_{degC}+273.15.
      $$
      
      脚本的输出温度仍然是 `degC`，只有进入 `D` 公式的指数项时才加 `273.15`。`material_properties()` 对用于除法的 `C` 使用不小于 `1e-12` 的数值下限；Picard 收敛后对极小的数值负值作非负截断。这是数值保护，不是新的物性模型。
      
      ## 7. 模型假设和适用范围
      
      当前结果建立在以下假设上：
      
      1. 药材是均匀、各向同性的规则圆柱，空间上只考虑径向变化。
      2. 轴向梯度、两个端面的传热传质、内部孔隙的复杂结构和二维/三维效应均忽略。
      3. `R=2 cm` 在整个问题二计算期间保持不变，不考虑干燥收缩；收缩只应在问题四中按附件 2 和附录 4 单独建模。
      4. 初始温度 `28 degC` 和初始含水率 `2.55 kg/kg` 在整个半径内均匀。
      5. `h` 和 `h_m` 沿表面均匀，并在问题二计算中保持问题一的数值；没有重新反演或优化传递系数。
      6. 烘房温度和烘房水分浓度在药材表面空间上均匀；附件 1 中的 `水分浓度` 直接作为 `C_air(t)` 使用，不进行湿空气热力学换算。
      7. 不加入蒸发潜热、辐射换热、内部热源、化学反应或相变动力学；温度对水分的影响只通过附录 3 的 `D(T,C)` 体现。
      8. 不加入半径变化、移动网格或轴向流动等问题四内容。
      9. 当前使用附录 3 经验式覆盖整个 3 h 区间，不额外给动态物性做参数拟合。
      
      这些假设使问题二保持为固定几何下的热质耦合扩散问题；如果后续模型改变边界、几何或潜热处理，不能把新结果与当前结果直接混用。
      
      ## 8. 附件 1 烘房边界数据
      
      `load_air_data()` 读取 `problem/附件/附件1.xlsx` 中的三列：`时间`、`温度`、`水分浓度`。当前附件数据覆盖 `0--14400 s`，求解的 `0--10800 s` 完全位于数据范围内。
      
      读取后程序将三列转为数值、按时间排序，并对重复时间保留最后一条；随后使用 `numpy.interp` 对 `T_air(t)` 和 `C_air(t)` 进行分段线性插值。每个后向欧拉步在 `time_new_s` 处取边界值。
      
      因此，当前版本使用附件 1 的完整边界记录，包括 `1800 s` 之后的实际数据；不是把 `1800 s` 之后的边界冻结为 `1800 s` 末值。这个区别是最新提交 `ed97452` 修正的重点。
      
      ## 9. 径向有限体积离散
      
      ### 9.1 网格和控制体积
      
      内部节点包含 `r=0` 和 `r=R`：
      
      $$
      \Delta r=0.000125\ \mathrm{m}=0.0125\ \mathrm{cm},
      $$
      
      共 `161` 个节点。相邻节点面取算术中点：
      
      $$
      r_{i+1/2}=\frac{r_i+r_{i+1}}{2}.
      $$
      
      去掉公共因子 `2 pi L` 后，第 `i` 个控制体积的径向测度为：
      
      $$
      V_i^{(r)}=\int_{r_{i-1/2}}^{r_{i+1/2}}r\,dr
      =\frac{r_{i+1/2}^2-r_{i-1/2}^2}{2}.
      $$
      
      首尾节点是半控制体积，内部节点是完整控制体积。
      
      ### 9.2 内部面通量和面物性
      
      温度内部面的导热系数取相邻节点算术平均：
      
      $$
      k_{i+1/2}=\frac{k_i+k_{i+1}}{2},
      $$
      
      对应的径向导热通量系数为：
      
      $$
      G^T_{i+1/2}=k_{i+1/2}\frac{r_{i+1/2}}{\Delta r}.
      $$
      
      水分面扩散系数同样取算术平均：
      
      $$
      D_{i+1/2}=\frac{D_i+D_{i+1}}{2},
      \qquad
      G^C_{i+1/2}=D_{i+1/2}\frac{r_{i+1/2}}{\Delta r}.
      $$
      
      由相邻控制体积共享同一面通量，内部离散保持守恒。
      
      ### 9.3 中心和表面
      
      `r=0` 的内侧面因面半径为零，通量自然为零；代码不计算 `1/r`，因此不会出现中心除零。对常系数情形，这种半控制体积处理等价于中心极限中的
      
      $$
      \left.\frac{1}{r}\frac{\partial}{\partial r}
      \left(r\frac{\partial T}{\partial r}\right)\right|_{r=0}
      \approx\frac{4(T_1-T_0)}{\Delta r^2}.
      $$
      
      表面最后一个半控制体积的外侧面不再假设零通量，而是直接代入热/质 Robin 边界。这样既保留了半控制体积的几何测度，也使边界换热和传质项具有正确方向。
      
      线性系统均为三对角系统，使用 `scipy.linalg.solve_banded` 求解。
      
      ## 10. 后向欧拉和 Picard 非线性流程
      
      最终计算使用 `dt=1 s`、后向欧拉。对从 `t^n` 到 `t^(n+1)` 的每一步，流程如下：
      
      1. 令 `T^(0)=T^n`、`C^(0)=C^n`。
      2. 用当前猜测 `T^(m)`、`C^(m)` 计算所有节点的 `rho`、`cp`、`k`、`D`，并在相邻面取面系数。
      3. 冻结这些物性，分别组装并求解后向欧拉温度三对角系统和水分三对角系统，得到临时 `T^(m+1)`、`C^(m+1)`。
      4. 计算
      
         $$
         \max_i|T_i^{(m+1)}-T_i^{(m)}|,
         \qquad
         \max_i|C_i^{(m+1)}-C_i^{(m)}|.
         $$
      
      5. 当温度差不超过 `1e-8 degC` 且水分差不超过 `1e-10 kg/kg` 时，接受当前时间步；否则将临时状态作为新的猜测继续迭代。
      6. 单步最大迭代次数为 `50`。当前 3 h 运行最大只用到 `4` 次，平均 `3.8219444444` 次。
      
      两场在每次 Picard 外迭代中使用同一组冻结状态求解，再一起更新；这保证 `D(T,C)`、`rho(C)`、`cp(C)`、`k(C)` 在一个时间步内不是只按初始状态计算一次。
      
      ## 11. 时间、空间和输出结构
      
      - 内部时间步：`dt=1 s`；
      - 总时长：`10800 s`；
      - 输出时间：`0,1,...,10800 s`，共 `10801` 个时刻；
      - 输出半径：`0,0.1,...,2.0 cm`，共 `21` 个位置；这些位置正好落在内部网格上，不需要额外空间插值；
      - `result2.xlsx`：只保留模板要求的 `温度`、`水分浓度` 两个工作表；A 列为时间（s），第 1 行为到中心距离（cm），数值按四位小数写出；
      - `task2_all_results.csv`：列为 `time_s,time_h,radius_cm,temperature_C,moisture_kgkg`，每个 `(time,radius)` 一行，共 `10801*21=226821` 条数据记录，`time_h` 仅为辅助字段。
      
      计算内部保留双精度，答案文件的温度和水分值统一按题目要求保留四位小数。
      
      ## 12. 当前结果和数值验证
      
      对当前脚本执行 `--no-write` 的完整 3 h 运行，得到：
      
      - 完整推进到 `10800 s`；
      - 温度范围：`27.999999999999872--49.9663867557243 degC`，按输出精度为 `28.0000--49.9664 degC`；
      - 水分范围：`1.0081299103327388--2.5500000000000047 kg/kg`，按输出精度为 `1.0081--2.5500 kg/kg`；
      - 无 NaN、Inf 或明显负水分；
      - 最大 Picard 次数为 `4`，平均次数为 `3.8219444444`；
      - 末时刻表面比中心高 `0.1169551 degC`，表面含水率比中心低 `0.7580687 kg/kg`，符合表面先升温、先失水的径向响应；
      - 相邻输出时刻没有超过脚本 sanity check 阈值的温度/水分跳变。
      
      时间步敏感性是在表 3、表 4 的六个时间点和五个径向位置上比较 `dt=1 s` 与 `dt=0.5 s`：
      
      - 最大温度绝对差：`7.381804e-4 degC`，出现在 `(t,r)=(1800 s,0 cm)`；
      - 最大水分绝对差：`4.569464e-5 kg/kg`，出现在 `(t,r)=(1800 s,2 cm)`。
      
      因此当前结果保留题目要求的 `dt=1 s`。这是关键点集合上的低成本检查，不应表述为所有内部时间/空间点的严格误差上界。
      
      答案一致性检查结果：
      
      - CSV 读取到 `226821` 条数据记录，全部温度和水分值有限；
      - XLSX 工作表严格为 `温度`、`水分浓度`，每张表为 `10802` 行（含表头）和 `22` 列（含时间列）；
      - XLSX 与 CSV 在全部 `10801*21` 个温度/水分位置的最大绝对差均为 `0`（两者都读取四位小数结果）；
      - XLSX 的起始时间为 `0`、末时间为 `10800`，距离表头为 `0--2.0 cm`。
      
      ## 13. 表 3 和表 4 当前结果
      
      以下数值均直接从当前完整 CSV（同时也是当前 XLSX 的数值场）提取，单位和表头与题目一致。
      
      ### 表 3：温度（degC）
      
      | 时间/h | 0 cm | 0.5 cm | 1.0 cm | 1.5 cm | 2.0 cm |
      |---:|---:|---:|---:|---:|---:|
      | 0.5 | 32.1907 | 32.3836 | 32.9673 | 33.9620 | 35.4140 |
      | 1.0 | 40.3816 | 40.5536 | 41.0605 | 41.8783 | 42.9978 |
      | 1.5 | 45.8461 | 45.9342 | 46.1924 | 46.6045 | 47.1396 |
      | 2.0 | 48.4497 | 48.4875 | 48.5980 | 48.7731 | 49.0030 |
      | 2.5 | 49.4666 | 49.4789 | 49.5133 | 49.5652 | 49.6610 |
      | 3.0 | 49.8494 | 49.8553 | 49.8745 | 49.9101 | 49.9664 |
      
      ### 表 4：水分浓度（kg/kg）
      
      | 时间/h | 0 cm | 0.5 cm | 1.0 cm | 1.5 cm | 2.0 cm |
      |---:|---:|---:|---:|---:|---:|
      | 0.5 | 2.5499 | 2.5489 | 2.5255 | 2.3257 | 1.6487 |
      | 1.0 | 2.5257 | 2.4947 | 2.3578 | 2.0230 | 1.4711 |
      | 1.5 | 2.3860 | 2.3256 | 2.1344 | 1.8020 | 1.3476 |
      | 2.0 | 2.1708 | 2.1084 | 1.9236 | 1.6260 | 1.2311 |
      | 2.5 | 1.9567 | 1.9006 | 1.7360 | 1.4720 | 1.1167 |
      | 3.0 | 1.7662 | 1.7166 | 1.5702 | 1.3333 | 1.0081 |
      
      ## 14. 运行方式和函数入口
      
      在项目根目录执行完整求解（会写入两个答案文件）：
      
      ```bash
      /Users/jiaqiaosu/miniconda3/bin/python solution/task2/script/solve_task2.py
      ```
      
      只运行求解和检查、不改写答案文件：
      
      ```bash
      /Users/jiaqiaosu/miniconda3/bin/python solution/task2/script/solve_task2.py --no-write
      ```
      
      跳过 `dt=0.5 s` 敏感性检查：
      
      ```bash
      /Users/jiaqiaosu/miniconda3/bin/python solution/task2/script/solve_task2.py --no-write --skip-sensitivity
      ```
      
      脚本的主要入口函数为：
      
      - `load_air_data()`：读取附件 1 并返回完整边界数据；
      - `control_volume_geometry()`：建立节点、面和半控制体积测度；
      - `material_properties()`：按当前 `T,C` 计算四个动态物性；
      - `_solve_temperature_linear()`、`_solve_moisture_linear()`：求解冻结物性下的单步线性系统；
      - `_picard_step()`：完成单个时间步的 Picard 迭代；
      - `solve_task2()`：推进完整时间区间并保存输出网格上的数值场；
      - `validate_solution()`：执行形状、有限值、初值、边界响应和跳变检查；
      - `write_result_xlsx()`、`write_result_csv()`：生成两个结果文件；
      - `key_tables()`：从完整场提取表 3、表 4；
      - `time_step_sensitivity()`：比较 `dt=1 s` 和 `dt=0.5 s` 的关键点结果。
      
      默认运行会覆盖：
      
      - `solution/task2/answer/result2.xlsx`；
      - `solution/task2/answer/task2_all_results.csv`。
      
      如果只是检查代码或复现实验统计，应使用 `--no-write`，避免覆盖当前答案文件。模板 `problem/附件/附件3/result2.xlsx` 和附件 1 均只读使用，不能直接改写模板。
      
      ## 15. 对后续问题三的交接注意事项
      
      问题三可以复用本问题二的固定半径核心：附录 3 动态物性、径向有限体积、中心零通量、表面对流传质、后向欧拉和 Picard 迭代。问题三仍然不应直接引入问题四的尺寸收缩；不要把附件 2 半径数据或附录 4 物性公式混入问题三。
      
      如果问题三需要把时间范围延长到 3 h 之外，应先根据题面确认烘房边界条件如何延拓。当前问题二仅使用附件 1 的 `0--14400 s` 数据计算到 `10800 s`，不能把这个 3 h 结果文件的边界处理未经检查地外推到更长时间。问题四才单独处理半径随水分变化的移动几何和相关经验公式。

## Assistant

已确认基线：仓库中已有可运行的 `task2`、`task3`。问题三当前真实实现采用固定半径、后向欧拉、Picard、径向有限体积，长期环境在附件 1 末点后保持末值；我会以代码和最新 task3 验收证据为准，不采用旧 handoff 中与代码不一致的“稳定段平均值”说法。

当前工作树已有与本任务无关的 staged/untracked 文件和 `.DS_Store`，后续提交只允许包含 `solution/task4/`，不会触碰这些既有改动。

## Activity

    $ /bin/zsh -lc "sed -n '1,280p' /Users/jiaqiaosu/.agents/skills/subagent-driven-development/SKILL.md"
    status: Completed · exit 0
      ---
      name: subagent-driven-development
      description: Use when executing implementation plans with independent tasks in the current session
      ---
      
      # Subagent-Driven Development
      
      Execute plan by dispatching fresh subagent per task, with two-stage review after each: spec compliance review first, then code quality review.
      
      **Why subagents:** You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.
      
      **Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration
      
      **Continuous execution:** Do not pause to check in with your human partner between tasks. Execute all tasks from the plan without stopping. The only reasons to stop are: BLOCKED status you cannot resolve, ambiguity that genuinely prevents progress, or all tasks complete. "Should I continue?" prompts and progress summaries waste their time — they asked you to execute the plan, so execute it.
      
      ## When to Use
      
      ```dot
      digraph when_to_use {
          "Have implementation plan?" [shape=diamond];
          "Tasks mostly independent?" [shape=diamond];
          "Stay in this session?" [shape=diamond];
          "subagent-driven-development" [shape=box];
          "executing-plans" [shape=box];
          "Manual execution or brainstorm first" [shape=box];
      
          "Have implementation plan?" -> "Tasks mostly independent?" [label="yes"];
          "Have implementation plan?" -> "Manual execution or brainstorm first" [label="no"];
          "Tasks mostly independent?" -> "Stay in this session?" [label="yes"];
          "Tasks mostly independent?" -> "Manual execution or brainstorm first" [label="no - tightly coupled"];
          "Stay in this session?" -> "subagent-driven-development" [label="yes"];
          "Stay in this session?" -> "executing-plans" [label="no - parallel session"];
      }
      ```
      
      **vs. Executing Plans (parallel session):**
      - Same session (no context switch)
      - Fresh subagent per task (no context pollution)
      - Two-stage review after each task: spec compliance first, then code quality
      - Faster iteration (no human-in-loop between tasks)
      
      ## The Process
      
      ```dot
      digraph process {
          rankdir=TB;
      
          subgraph cluster_per_task {
              label="Per Task";
              "Dispatch implementer subagent (./implementer-prompt.md)" [shape=box];
              "Implementer subagent asks questions?" [shape=diamond];
              "Answer questions, provide context" [shape=box];
              "Implementer subagent implements, tests, commits, self-reviews" [shape=box];
              "Dispatch spec reviewer subagent (./spec-reviewer-prompt.md)" [shape=box];
              "Spec reviewer subagent confirms code matches spec?" [shape=diamond];
              "Implementer subagent fixes spec gaps" [shape=box];
              "Dispatch code quality reviewer subagent (./code-quality-reviewer-prompt.md)" [shape=box];
              "Code quality reviewer subagent approves?" [shape=diamond];
              "Implementer subagent fixes quality issues" [shape=box];
              "Mark task complete in TodoWrite" [shape=box];
          }
      
          "Read plan, extract all tasks with full text, note context, create TodoWrite" [shape=box];
          "More tasks remain?" [shape=diamond];
          "Dispatch final code reviewer subagent for entire implementation" [shape=box];
          "Use superpowers:finishing-a-development-branch" [shape=box style=filled fillcolor=lightgreen];
      
          "Read plan, extract all tasks with full text, note context, create TodoWrite" -> "Dispatch implementer subagent (./implementer-prompt.md)";
          "Dispatch implementer subagent (./implementer-prompt.md)" -> "Implementer subagent asks questions?";
          "Implementer subagent asks questions?" -> "Answer questions, provide context" [label="yes"];
          "Answer questions, provide context" -> "Dispatch implementer subagent (./implementer-prompt.md)";
          "Implementer subagent asks questions?" -> "Implementer subagent implements, tests, commits, self-reviews" [label="no"];
          "Implementer subagent implements, tests, commits, self-reviews" -> "Dispatch spec reviewer subagent (./spec-reviewer-prompt.md)";
          "Dispatch spec reviewer subagent (./spec-reviewer-prompt.md)" -> "Spec reviewer subagent confirms code matches spec?";
          "Spec reviewer subagent confirms code matches spec?" -> "Implementer subagent fixes spec gaps" [label="no"];
          "Implementer subagent fixes spec gaps" -> "Dispatch spec reviewer subagent (./spec-reviewer-prompt.md)" [label="re-review"];
          "Spec reviewer subagent confirms code matches spec?" -> "Dispatch code quality reviewer subagent (./code-quality-reviewer-prompt.md)" [label="yes"];
          "Dispatch code quality reviewer subagent (./code-quality-reviewer-prompt.md)" -> "Code quality reviewer subagent approves?";
          "Code quality reviewer subagent approves?" -> "Implementer subagent fixes quality issues" [label="no"];
          "Implementer subagent fixes quality issues" -> "Dispatch code quality reviewer subagent (./code-quality-reviewer-prompt.md)" [label="re-review"];
          "Code quality reviewer subagent approves?" -> "Mark task complete in TodoWrite" [label="yes"];
          "Mark task complete in TodoWrite" -> "More tasks remain?";
          "More tasks remain?" -> "Dispatch implementer subagent (./implementer-prompt.md)" [label="yes"];
          "More tasks remain?" -> "Dispatch final code reviewer subagent for entire implementation" [label="no"];
          "Dispatch final code reviewer subagent for entire implementation" -> "Use superpowers:finishing-a-development-branch";
      }
      ```
      
      ## Model Selection
      
      Use the least powerful model that can handle each role to conserve cost and increase speed.
      
      **Mechanical implementation tasks** (isolated functions, clear specs, 1-2 files): use a fast, cheap model. Most implementation tasks are mechanical when the plan is well-specified.
      
      **Integration and judgment tasks** (multi-file coordination, pattern matching, debugging): use a standard model.
      
      **Architecture, design, and review tasks**: use the most capable available model.
      
      **Task complexity signals:**
      - Touches 1-2 files with a complete spec → cheap model
      - Touches multiple files with integration concerns → standard model
      - Requires design judgment or broad codebase understanding → most capable model
      
      ## Handling Implementer Status
      
      Implementer subagents report one of four statuses. Handle each appropriately:
      
      **DONE:** Proceed to spec compliance review.
      
      **DONE_WITH_CONCERNS:** The implementer completed the work but flagged doubts. Read the concerns before proceeding. If the concerns are about correctness or scope, address them before review. If they're observations (e.g., "this file is getting large"), note them and proceed to review.
      
      **NEEDS_CONTEXT:** The implementer needs information that wasn't provided. Provide the missing context and re-dispatch.
      
      **BLOCKED:** The implementer cannot complete the task. Assess the blocker:
      1. If it's a context problem, provide more context and re-dispatch with the same model
      2. If the task requires more reasoning, re-dispatch with a more capable model
      3. If the task is too large, break it into smaller pieces
      4. If the plan itself is wrong, escalate to the human
      
      **Never** ignore an escalation or force the same model to retry without changes. If the implementer said it's stuck, something needs to change.
      
      ## Prompt Templates
      
      - `./implementer-prompt.md` - Dispatch implementer subagent
      - `./spec-reviewer-prompt.md` - Dispatch spec compliance reviewer subagent
      - `./code-quality-reviewer-prompt.md` - Dispatch code quality reviewer subagent
      
      ## Example Workflow
      
      ```
      You: I'm using Subagent-Driven Development to execute this plan.
      
      [Read plan file once: docs/superpowers/plans/feature-plan.md]
      [Extract all 5 tasks with full text and context]
      [Create TodoWrite with all tasks]
      
      Task 1: Hook installation script
      
      [Get Task 1 text and context (already extracted)]
      [Dispatch implementation subagent with full task text + context]
      
      Implementer: "Before I begin - should the hook be installed at user or system level?"
      
      You: "User level (~/.config/superpowers/hooks/)"
      
      Implementer: "Got it. Implementing now..."
      [Later] Implementer:
        - Implemented install-hook command
        - Added tests, 5/5 passing
        - Self-review: Found I missed --force flag, added it
        - Committed
      
      [Dispatch spec compliance reviewer]
      Spec reviewer: ✅ Spec compliant - all requirements met, nothing extra
      
      [Get git SHAs, dispatch code quality reviewer]
      Code reviewer: Strengths: Good test coverage, clean. Issues: None. Approved.
      
      [Mark Task 1 complete]
      
      Task 2: Recovery modes
      
      [Get Task 2 text and context (already extracted)]
      [Dispatch implementation subagent with full task text + context]
      
      Implementer: [No questions, proceeds]
      Implementer:
        - Added verify/repair modes
        - 8/8 tests passing
        - Self-review: All good
        - Committed
      
      [Dispatch spec compliance reviewer]
      Spec reviewer: ❌ Issues:
        - Missing: Progress reporting (spec says "report every 100 items")
        - Extra: Added --json flag (not requested)
      
      [Implementer fixes issues]
      Implementer: Removed --json flag, added progress reporting
      
      [Spec reviewer reviews again]
      Spec reviewer: ✅ Spec compliant now
      
      [Dispatch code quality reviewer]
      Code reviewer: Strengths: Solid. Issues (Important): Magic number (100)
      
      [Implementer fixes]
      Implementer: Extracted PROGRESS_INTERVAL constant
      
      [Code reviewer reviews again]
      Code reviewer: ✅ Approved
      
      [Mark Task 2 complete]
      
      ...
      
      [After all tasks]
      [Dispatch final code-reviewer]
      Final reviewer: All requirements met, ready to merge
      
      Done!
      ```
      
      ## Advantages
      
      **vs. Manual execution:**
      - Subagents follow TDD naturally
      - Fresh context per task (no confusion)
      - Parallel-safe (subagents don't interfere)
      - Subagent can ask questions (before AND during work)
      
      **vs. Executing Plans:**
      - Same session (no handoff)
      - Continuous progress (no waiting)
      - Review checkpoints automatic
      
      **Efficiency gains:**
      - No file reading overhead (controller provides full text)
      - Controller curates exactly what context is needed
      - Subagent gets complete information upfront
      - Questions surfaced before work begins (not after)
      
      **Quality gates:**
      - Self-review catches issues before handoff
      - Two-stage review: spec compliance, then code quality
      - Review loops ensure fixes actually work
      - Spec compliance prevents over/under-building
      - Code quality ensures implementation is well-built
      
      **Cost:**
      - More subagent invocations (implementer + 2 reviewers per task)
      - Controller does more prep work (extracting all tasks upfront)
      - Review loops add iterations
      - But catches issues early (cheaper than debugging later)
      
      ## Red Flags
      
      **Never:**
      - Start implementation on main/master branch without explicit user consent
      - Skip reviews (spec compliance OR code quality)
      - Proceed with unfixed issues
      - Dispatch multiple implementation subagents in parallel (conflicts)
      - Make subagent read plan file (provide full text instead)
      - Skip scene-setting context (subagent needs to understand where task fits)
      - Ignore subagent questions (answer before letting them proceed)
      - Accept "close enough" on spec compliance (spec reviewer found issues = not done)
      - Skip review loops (reviewer found issues = implementer fixes = review again)
      - Let implementer self-review replace actual review (both are needed)
      - **Start code quality review before spec compliance is ✅** (wrong order)
      - Move to next task while either review has open issues
      
      **If subagent asks questions:**
      - Answer clearly and completely
      - Provide additional context if needed
      - Don't rush them into implementation
      
      **If reviewer finds issues:**
      - Implementer (same subagent) fixes them
      - Reviewer reviews again
      - Repeat until approved
      - Don't skip the re-review
      
      **If subagent fails task:**
      - Dispatch fix subagent with specific instructions
      - Don't try to fix manually (context pollution)
      
      ## Integration
      
      **Required workflow skills:**
      - **superpowers:using-git-worktrees** - Ensures isolated workspace (creates one or verifies existing)
      - **superpowers:writing-plans** - Creates the plan this skill executes
      - **superpowers:requesting-code-review** - Code review template for reviewer subagents
      - **superpowers:finishing-a-development-branch** - Complete development after all tasks
      
      **Subagents should use:**
      - **superpowers:test-driven-development** - Subagents follow TDD for each task
      
      **Alternative workflow:**
      - **superpowers:executing-plans** - Use for parallel session instead of same-session execution

## Activity

    agent tool: Wait · Completed

## Assistant

阶段一仍在进行。当前最关键的建模结论已经明确：令 \(\hat T(\xi,t)=T(R(t)\xi,t)\)、\(\hat C(\xi,t)=C(R(t)\xi,t)\)，则固定物理坐标时间导数满足
\[
\partial_t T|_r=\partial_t\hat T|_\xi-\frac{\dot R}{R}\xi\,\partial_\xi\hat T
\]
（水分同理），扩散算子缩放为 \(1/R^2\)。后续实现必须显式离散这一移动坐标项，不能只替换半径参数。当前在等附件 2 和官方模板的精确语义检查结果。

## Activity

    agent tool: Wait · Completed

## Activity

    Interacted with `/root/task4_phase1`

## Activity

    Completed `/root/task4_phase1`

## Activity

    agent tool: Wait · Completed

## Assistant

阶段一结论：附件 2 覆盖 `0–259200 s`，半径从 `2.000 cm` 单调收缩至 `1.198 cm`；预计结束时仍在数据覆盖内，无需外推。官方 `result4.xlsx` 明确保留“药材表面”动态列，因此固定绝对坐标超出当前半径时将留空，另写真实 \(r=R(t)\) 表面值。

实施方案已锁定：固定 \(\xi\) 网格、后向欧拉、Picard；每步用 \([R(t_{n+1})-R(t_n)]/\Delta t\) 计算与分段线性插值一致的 \(\dot R\)，移动项采用稳定的迎风离散；终止时刻在首次跨阈值的时间步内二分加密。现在进入首个可运行版本实现。`writing-plans` 生成的执行计划只放临时目录，不向仓库加入内部规划文件。

## Activity

    Started `/root/task4_solver`

## Activity

    agent tool: Wait · Completed

## Assistant

求解器正在实现并跑首个全程基线。验收时我会特别检查两处容易导致“结果看似合理但方程错误”的细节：

1. 采用物理控制体测度 \(R^2\!\int \xi\,d\xi\) 时，表面 Robin 项必须是 \(R\,h\) 与 \(R\,h_m\)，而不是沿用固定半径常量。
2. 收缩项写成 \(b\xi\,\partial_\xi\)（\(b=-\dot R/R\ge0\)）放在左侧后，迎风方向应取后差；符号反了会人为加速或减慢内部水分迁移。

首轮结果出来后，我会先审代码和离散量纲，再允许生成提交文件。

## Activity

    agent tool: Wait · Completed

## Activity

    agent tool: Wait · Completed

## Activity

    Interacted with `/root/task4_solver`

## Activity

    $ /bin/zsh -lc "git status --short && git diff -- solution/task4/script/solve_task4.py | sed -n '1,320p' && ps -axo pid,etime,command | rg 'solve_task4|python' | tail -20"
    status: Completed · exit 0
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/
      ?? solution/task4/
      zsh:1: operation not permitted: ps

## Assistant

当前发现一个需要立即核对的 Git 状态变化：先前已有的 staged `context/handoff` 文件不再出现在 `git status` 中。由于它们不属于 task4，我正在确认是否被其他并发工作提交或状态被改变；在确认前不会接受任何 task4 提交。求解脚本已出现在未跟踪目录中，但尚未据此认定阶段完成。

## Activity

    $ /bin/zsh -lc "git log --oneline -n 8 && git status --short --branch && find solution/task4 -maxdepth 3 -type f -print -exec wc -l {} \\; && sed -n '1,360p' solution/task4/script/solve_task4.py"
    status: Completed · exit 0
      4040291 补充任务三交接文档
      b5eb0bb 补充问题二与问题三交接文档
      735fbbd 生成问题三完整结果文件并通过验证
      b5a750c 优化问题三答案文件验证读取
      1f53b08 新增问题三长期烘干求解器
      e3f08be 修正问题二交接文档时间离散表述
      f90d788 补充问题二数值模型交接文档
      ed97452 修正问题二烘房边界数据
      ## main...origin/main
      A  solution/task4/script/solve_task4.py
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/
      solution/task4/script/solve_task4.py
           899 solution/task4/script/solve_task4.py
      """A题问题四：药材收缩条件下的移动边界热湿耦合求解器。
      
      空间坐标采用固定的
      
          xi = r / R(t), 0 <= xi <= 1,
      
      并在固定 xi 网格上用径向控制体积法离散。时间方向采用后向欧拉；每个
      内部时间步内用 Picard 迭代更新附录 4 的状态相关物性。半径 R(t) 来自
      附件 2 的分段线性插值，移动坐标项 b*xi*T_xi（b=-Rdot/R）用一阶后向
      迎风差分，并与扩散项一起隐式求解。
      
      本阶段只负责数值状态和验证接口，不生成问题四 answer 文件。后续结果
      生成器可直接使用 solve_task4 返回的每 60 s 完整 xi 状态与终止状态。
      """
      
      from __future__ import annotations
      
      import argparse
      import time as wall_time
      from pathlib import Path
      from typing import Any
      
      import numpy as np
      import pandas as pd
      from scipy.linalg import solve_banded
      
      
      # 题目和问题二/三已确定的环境、初始条件及边界传递参数。
      RADIUS_INITIAL_M = 0.02
      LENGTH_M = 0.25
      INITIAL_TEMPERATURE_C = 28.0
      INITIAL_MOISTURE_KGKG = 2.55
      HEAT_TRANSFER_W_M2_K = 25.0
      MASS_TRANSFER_M_S = 8.0e-7
      
      # 问题四数值默认值。
      N_DEFAULT = 160  # xi 区间数，dxi=1/160
      TIME_STEP_S_DEFAULT = 1.0
      OUTPUT_DT_S = 60.0
      DRYING_THRESHOLD_KGKG = 0.15
      EVENT_TOL_S = 1.0e-3
      
      PICARD_TOL_T_C = 1.0e-8
      PICARD_TOL_C_KGKG = 1.0e-10
      PICARD_MAX_ITER = 50
      
      REPO_ROOT = Path(__file__).resolve().parents[3]
      DEFAULT_AIR_DATA_PATH = REPO_ROOT / "problem" / "附件" / "附件1.xlsx"
      DEFAULT_RADIUS_DATA_PATH = REPO_ROOT / "problem" / "附件" / "附件2.xlsx"
      # 附件 2 的最后一个数据时刻；求解不会超出该时刻，也不会外推 R(t)。
      DEFAULT_MAX_TIME_S = 259200.0
      
      
      def _required_columns(frame: pd.DataFrame, required: tuple[str, ...]) -> dict[str, Any]:
          """按去除首尾空格后的中文列名返回原始列映射。"""
      
          mapping = {str(column).strip(): column for column in frame.columns}
          missing = [name for name in required if name not in mapping]
          if missing:
              raise ValueError(
                  f"附件缺少必需列 {missing!r}；实际列为 {list(frame.columns)!r}"
              )
          return mapping
      
      
      def load_air_data(
          path: str | Path = DEFAULT_AIR_DATA_PATH,
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
          """读取附件 1；求解区间外的边界值由 np.interp 保持末值。"""
      
          frame = pd.read_excel(Path(path))
          columns = _required_columns(frame, ("时间", "温度", "水分浓度"))
          selected = frame[[columns["时间"], columns["温度"], columns["水分浓度"]]].copy()
          selected.columns = ["时间", "温度", "水分浓度"]
          for column in selected.columns:
              selected[column] = pd.to_numeric(selected[column], errors="raise")
          selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")
          time_s = selected["时间"].to_numpy(dtype=float)
          temperature_C = selected["温度"].to_numpy(dtype=float)
          moisture_kgkg = selected["水分浓度"].to_numpy(dtype=float)
          values = np.column_stack((time_s, temperature_C, moisture_kgkg))
          if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
              raise ValueError("附件1时间必须包含至少两个严格递增时间点")
          if time_s[0] > 1.0e-10 or not np.all(np.isfinite(values)):
              raise ValueError("附件1时间必须从0开始且数据必须有限")
          return time_s, temperature_C, moisture_kgkg
      
      
      def load_radius_data(
          path: str | Path = DEFAULT_RADIUS_DATA_PATH,
      ) -> tuple[np.ndarray, np.ndarray]:
          """读取附件 2 的时间/半径，并将半径从 cm 转为 m。"""
      
          frame = pd.read_excel(Path(path))
          columns = _required_columns(frame, ("时间", "半径"))
          selected = frame[[columns["时间"], columns["半径"]]].copy()
          selected.columns = ["时间", "半径"]
          for column in selected.columns:
              selected[column] = pd.to_numeric(selected[column], errors="raise")
          selected = selected.sort_values("时间").drop_duplicates("时间", keep="last")
          time_s = selected["时间"].to_numpy(dtype=float)
          radius_cm = selected["半径"].to_numpy(dtype=float)
          radius_m = radius_cm / 100.0
          values = np.column_stack((time_s, radius_cm, radius_m))
          if time_s.size < 2 or np.any(np.diff(time_s) <= 0.0):
              raise ValueError("附件2时间必须包含至少两个严格递增时间点")
          if time_s[0] > 1.0e-10 or not np.all(np.isfinite(values)):
              raise ValueError("附件2时间必须从0开始且数据必须有限")
          if np.any(radius_m <= 0.0):
              raise ValueError("附件2半径必须为正")
          if not np.isclose(radius_m[0], RADIUS_INITIAL_M, rtol=0.0, atol=1.0e-12):
              raise ValueError(
                  f"附件2初始半径为 {radius_cm[0]:g} cm，不是题设的 2 cm"
              )
          if np.any(np.diff(radius_m) > 1.0e-12):
              raise ValueError("附件2半径必须单调不增，不能为移动边界使用非物理膨胀数据")
          return time_s, radius_m
      
      
      def radius_at(time_s: float, radius_time_s: np.ndarray, radius_m: np.ndarray) -> float:
          """在附件2覆盖范围内分段线性插值 R(t)，不允许无说明外推。"""
      
          if time_s < radius_time_s[0] - 1.0e-10 or time_s > radius_time_s[-1] + 1.0e-10:
              raise ValueError(
                  f"求解时刻 {time_s:g}s 超出附件2的 [{radius_time_s[0]:g}, "
                  f"{radius_time_s[-1]:g}]s 覆盖范围，禁止外推半径"
              )
          clipped_time = min(max(float(time_s), float(radius_time_s[0])), float(radius_time_s[-1]))
          return float(np.interp(clipped_time, radius_time_s, radius_m))
      
      
      def _air_at(time_s: float, air_time_s: np.ndarray, values: np.ndarray) -> float:
          """附件1内分段线性，14400 s 后保持最后观测值。"""
      
          return float(np.interp(float(time_s), air_time_s, values))
      
      
      def fixed_xi_geometry(n_intervals: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
          """返回 xi 节点、xi 面、固定 xi 控制体测度和 dxi。"""
      
          if n_intervals < 2:
              raise ValueError("xi 区间数至少为2")
          dxi = 1.0 / float(n_intervals)
          xi = np.linspace(0.0, 1.0, n_intervals + 1)
          faces = 0.5 * (xi[:-1] + xi[1:])
          measure = np.empty_like(xi)
          measure[0] = 0.5 * faces[0] ** 2
          measure[1:-1] = 0.5 * (faces[1:] ** 2 - faces[:-1] ** 2)
          measure[-1] = 0.5 * (1.0 - faces[-1] ** 2)
          if not np.isclose(np.sum(measure), 0.5, rtol=0.0, atol=1.0e-14):
              raise ValueError("固定xi控制体测度未覆盖 [0,1] 的径向积分测度")
          return xi, faces, measure, dxi
      
      
      def material_properties(
          temperature_C: np.ndarray,
          moisture_kgkg: np.ndarray,
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
          """附录4物性；指数公式中的温度显式转换为 Kelvin。"""
      
          temperature_C = np.asarray(temperature_C, dtype=float)
          moisture_kgkg = np.asarray(moisture_kgkg, dtype=float)
          if temperature_C.shape != moisture_kgkg.shape:
              raise ValueError("温度和水分数组形状不一致")
          concentration = np.maximum(moisture_kgkg, 1.0e-12)
          temperature_K = temperature_C + 273.15
          if np.any(~np.isfinite(temperature_K)) or np.any(temperature_K <= 0.0):
              raise ValueError("附录4物性计算遇到非正或非有限 Kelvin 温度")
      
          rho = 760.0 + 90.0 * concentration
          cp = 1850.0 + 2150.0 * concentration / (concentration + 1.0)
          conductivity = 0.12 + 0.20 * concentration / (concentration + 1.0)
          diffusivity = 4.2e-4 * np.exp(-0.30 / concentration) * np.exp(
              -3850.0 / temperature_K
          )
          return rho, cp, conductivity, diffusivity
      
      
      def _harmonic_mean(left: np.ndarray, right: np.ndarray) -> np.ndarray:
          denominator = left + right
          if np.any(denominator <= 0.0):
              raise ValueError("界面物性必须为正")
          return 2.0 * left * right / denominator
      
      
      def _solve_tridiagonal(
          lower: np.ndarray,
          diagonal: np.ndarray,
          upper: np.ndarray,
          rhs: np.ndarray,
      ) -> np.ndarray:
          """解三对角系统；输入 lower/upper 长度为 n-1。"""
      
          n = diagonal.size
          banded = np.zeros((3, n), dtype=float)
          banded[0, 1:] = upper
          banded[1, :] = diagonal
          banded[2, :-1] = lower
          solution = solve_banded((1, 1), banded, rhs, check_finite=False)
          if not np.all(np.isfinite(solution)):
              raise RuntimeError("三对角线性系统求解得到 NaN 或 Inf")
          return solution
      
      
      def _assemble_temperature_system(
          old_temperature_C: np.ndarray,
          guess_temperature_C: np.ndarray,
          guess_moisture_kgkg: np.ndarray,
          xi: np.ndarray,
          faces: np.ndarray,
          measure: np.ndarray,
          dxi: float,
          radius_m: float,
          radius_rate_m_s: float,
          dt_s: float,
          air_temperature_C: float,
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
          """组装固定xi坐标下的温度后向欧拉矩阵。"""
      
          rho, cp, conductivity, _ = material_properties(
              guess_temperature_C, guess_moisture_kgkg
          )
          storage = rho * cp * measure
          face_conductivity = _harmonic_mean(conductivity[:-1], conductivity[1:])
          # 固定xi控制体扩散导通量：1/R^2 * xi_face*k_face/dxi。
          conductance = face_conductivity * faces / (radius_m**2 * dxi)
          b = -radius_rate_m_s / radius_m
          if b < -1.0e-12:
              raise ValueError("R(t)出现膨胀，不能继续使用 b>=0 的后向迎风差分")
          b = max(0.0, b)
          # PDE 的移动项为 b*xi*T_xi，b>=0 时使用 (T_j-T_{j-1})/dxi。
          advection = storage * b * xi / dxi
      
          diagonal = storage.copy()
          lower = np.zeros(storage.size - 1, dtype=float)
          upper = np.zeros(storage.size - 1, dtype=float)
          rhs = storage * old_temperature_C
          diagonal += dt_s * advection
          lower -= dt_s * advection[1:]
      
          # 中心自然零通量；中心项没有左邻接、没有移动项（xi=0）。
          diagonal[0] += dt_s * conductance[0]
          upper[0] -= dt_s * conductance[0]
          # 内部控制体。
          if storage.size > 2:
              left = conductance[:-1]
              right = conductance[1:]
              diagonal[1:-1] += dt_s * (left + right)
              # row j=1..n-2 的下/上三对角项分别对应 g_{j-1}/g_j。
              lower[:-1] -= dt_s * left
              upper[1:] -= dt_s * right
          # 移动表面 Robin：-(k/R)T_xi=h(Ts-Tair)，换成 h/R 的边界导通量。
          boundary_conductance = HEAT_TRANSFER_W_M2_K / radius_m
          diagonal[-1] += dt_s * (conductance[-1] + boundary_conductance)
          lower[-1] -= dt_s * conductance[-1]
          rhs[-1] += dt_s * boundary_conductance * air_temperature_C
          return lower, diagonal, upper, rhs
      
      
      def _assemble_moisture_system(
          old_moisture_kgkg: np.ndarray,
          guess_temperature_C: np.ndarray,
          guess_moisture_kgkg: np.ndarray,
          xi: np.ndarray,
          faces: np.ndarray,
          measure: np.ndarray,
          dxi: float,
          radius_m: float,
          radius_rate_m_s: float,
          dt_s: float,
          air_moisture_kgkg: float,
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
          """组装固定xi坐标下的水分后向欧拉矩阵。"""
      
          _, _, _, diffusivity = material_properties(
              guess_temperature_C, guess_moisture_kgkg
          )
          storage = measure.copy()
          face_diffusivity = _harmonic_mean(diffusivity[:-1], diffusivity[1:])
          conductance = face_diffusivity * faces / (radius_m**2 * dxi)
          b = -radius_rate_m_s / radius_m
          if b < -1.0e-12:
              raise ValueError("R(t)出现膨胀，不能继续使用 b>=0 的后向迎风差分")
          b = max(0.0, b)
          advection = storage * b * xi / dxi
      
          diagonal = storage.copy()
          lower = np.zeros(storage.size - 1, dtype=float)
          upper = np.zeros(storage.size - 1, dtype=float)
          rhs = storage * old_moisture_kgkg
          diagonal += dt_s * advection
          lower -= dt_s * advection[1:]
      
          diagonal[0] += dt_s * conductance[0]
          upper[0] -= dt_s * conductance[0]
          if storage.size > 2:
              left = conductance[:-1]
              right = conductance[1:]
              diagonal[1:-1] += dt_s * (left + right)
              lower[:-1] -= dt_s * left
              upper[1:] -= dt_s * right
          boundary_conductance = MASS_TRANSFER_M_S / radius_m
          diagonal[-1] += dt_s * (conductance[-1] + boundary_conductance)
          lower[-1] -= dt_s * conductance[-1]
          rhs[-1] += dt_s * boundary_conductance * air_moisture_kgkg
          return lower, diagonal, upper, rhs
      
      
      def _picard_step(
          old_temperature_C: np.ndarray,
          old_moisture_kgkg: np.ndarray,
          xi: np.ndarray,
          faces: np.ndarray,
          measure: np.ndarray,
          dxi: float,
          radius_old_m: float,
          radius_new_m: float,
          dt_s: float,
          air_temperature_C: float,
          air_moisture_kgkg: float,
      ) -> tuple[np.ndarray, np.ndarray, int, float, float]:
          """一个移动边界时间步内的 Picard 热湿耦合迭代。"""
      
          if dt_s <= 0.0:
              raise ValueError("Picard 时间步必须为正")
          radius_rate_m_s = (radius_new_m - radius_old_m) / dt_s
          guess_temperature_C = old_temperature_C.copy()
          guess_moisture_kgkg = old_moisture_kgkg.copy()
          last_delta_temperature = np.inf
          last_delta_moisture = np.inf
      
          for iteration in range(1, PICARD_MAX_ITER + 1):
              lower_T, diagonal_T, upper_T, rhs_T = _assemble_temperature_system(
                  old_temperature_C,
                  guess_temperature_C,
                  guess_moisture_kgkg,
                  xi,
                  faces,
                  measure,
                  dxi,
                  radius_new_m,
                  radius_rate_m_s,
                  dt_s,
                  air_temperature_C,
              )
              new_temperature_C = _solve_tridiagonal(
                  lower_T, diagonal_T, upper_T, rhs_T
              )
              lower_C, diagonal_C, upper_C, rhs_C = _assemble_moisture_system(
                  old_moisture_kgkg,
                  guess_temperature_C,
                  guess_moisture_kgkg,
                  xi,
                  faces,
                  measure,
                  dxi,
                  radius_new_m,
                  radius_rate_m_s,
                  dt_s,
                  air_moisture_kgkg,

## Activity

    $ /bin/zsh -lc "sed -n '360,940p' solution/task4/script/solve_task4.py"
    status: Completed · exit 0
                  air_moisture_kgkg,
              )
              new_moisture_kgkg = _solve_tridiagonal(
                  lower_C, diagonal_C, upper_C, rhs_C
              )
              last_delta_temperature = float(
                  np.max(np.abs(new_temperature_C - guess_temperature_C))
              )
              last_delta_moisture = float(
                  np.max(np.abs(new_moisture_kgkg - guess_moisture_kgkg))
              )
              if (
                  last_delta_temperature <= PICARD_TOL_T_C
                  and last_delta_moisture <= PICARD_TOL_C_KGKG
              ):
                  if np.min(new_moisture_kgkg) < -1.0e-10:
                      raise RuntimeError("Picard 步得到明显负水分浓度")
                  return (
                      new_temperature_C,
                      np.maximum(new_moisture_kgkg, 0.0),
                      iteration,
                      last_delta_temperature,
                      last_delta_moisture,
                  )
              guess_temperature_C = new_temperature_C
              guess_moisture_kgkg = new_moisture_kgkg
      
          raise RuntimeError(
              "问题四 Picard 迭代未收敛: "
              f"dt={dt_s:g}s, iter={PICARD_MAX_ITER}, "
              f"max|dT|={last_delta_temperature:.3e}, "
              f"max|dC|={last_delta_moisture:.3e}"
          )
      
      
      def _max_info(
          moisture_kgkg: np.ndarray,
          xi: np.ndarray,
          radius_m: float,
      ) -> tuple[float, int, float, float]:
          index = int(np.argmax(moisture_kgkg))
          maximum = float(moisture_kgkg[index])
          xi_position = float(xi[index])
          radius_position_m = xi_position * radius_m
          return maximum, index, xi_position, radius_position_m
      
      
      def _event_bisection(
          lower_time_s: float,
          lower_temperature_C: np.ndarray,
          lower_moisture_kgkg: np.ndarray,
          lower_max_kgkg: float,
          upper_time_s: float,
          upper_temperature_C: np.ndarray,
          upper_moisture_kgkg: np.ndarray,
          upper_max_kgkg: float,
          xi: np.ndarray,
          faces: np.ndarray,
          measure: np.ndarray,
          dxi: float,
          radius_time_s: np.ndarray,
          radius_m: np.ndarray,
          air_time_s: np.ndarray,
          air_temperature_C: np.ndarray,
          air_moisture_kgkg: np.ndarray,
      ) -> dict[str, Any]:
          """首次跨阈值后，用同一前一状态的局部时间段二分终止时刻。"""
      
          if not (lower_max_kgkg >= DRYING_THRESHOLD_KGKG):
              raise ValueError("事件二分下端不在阈值上方")
          if not (upper_max_kgkg < DRYING_THRESHOLD_KGKG):
              raise ValueError("事件二分上端未严格低于阈值")
          lower_time = float(lower_time_s)
          upper_time = float(upper_time_s)
          lower_temperature = lower_temperature_C.copy()
          lower_moisture = lower_moisture_kgkg.copy()
          lower_max = float(lower_max_kgkg)
          upper_temperature = upper_temperature_C.copy()
          upper_moisture = upper_moisture_kgkg.copy()
          upper_max = float(upper_max_kgkg)
      
          while upper_time - lower_time > EVENT_TOL_S:
              midpoint = 0.5 * (lower_time + upper_time)
              midpoint_radius = radius_at(midpoint, radius_time_s, radius_m)
              old_radius = radius_at(lower_time, radius_time_s, radius_m)
              midpoint_temperature, midpoint_moisture, _, _, _ = _picard_step(
                  lower_temperature,
                  lower_moisture,
                  xi,
                  faces,
                  measure,
                  dxi,
                  old_radius,
                  midpoint_radius,
                  midpoint - lower_time,
                  _air_at(midpoint, air_time_s, air_temperature_C),
                  _air_at(midpoint, air_time_s, air_moisture_kgkg),
              )
              midpoint_max, _, _, _ = _max_info(
                  midpoint_moisture, xi, midpoint_radius
              )
              if midpoint_max < DRYING_THRESHOLD_KGKG:
                  upper_time = midpoint
                  upper_temperature = midpoint_temperature
                  upper_moisture = midpoint_moisture
                  upper_max = midpoint_max
              else:
                  lower_time = midpoint
                  lower_temperature = midpoint_temperature
                  lower_moisture = midpoint_moisture
                  lower_max = midpoint_max
      
          upper_radius = radius_at(upper_time, radius_time_s, radius_m)
          maximum, index, xi_position, radius_position_m = _max_info(
              upper_moisture, xi, upper_radius
          )
          lower_radius = radius_at(lower_time, radius_time_s, radius_m)
          lower_max_check, lower_index, lower_xi, lower_position_m = _max_info(
              lower_moisture, xi, lower_radius
          )
          if not np.isclose(maximum, upper_max, rtol=0.0, atol=1.0e-12):
              raise RuntimeError("事件二分上端最大值记录不一致")
          if not np.isclose(lower_max_check, lower_max, rtol=0.0, atol=1.0e-12):
              raise RuntimeError("事件二分下端最大值记录不一致")
          return {
              "termination_time_s": float(upper_time),
              "termination_temperature_internal_C": upper_temperature,
              "termination_moisture_internal_kgkg": upper_moisture,
              "termination_max_kgkg": float(maximum),
              "termination_max_index": int(index),
              "termination_max_xi": float(xi_position),
              "termination_max_radius_m": float(radius_position_m),
              "termination_radius_m": float(upper_radius),
              "termination_lower_time_s": float(lower_time),
              "termination_lower_temperature_internal_C": lower_temperature,
              "termination_lower_moisture_internal_kgkg": lower_moisture,
              "termination_lower_max_kgkg": float(lower_max_check),
              "termination_lower_max_index": int(lower_index),
              "termination_lower_max_xi": float(lower_xi),
              "termination_lower_max_radius_m": float(lower_position_m),
              "termination_lower_radius_m": float(lower_radius),
              "termination_bracket_width_s": float(upper_time - lower_time),
          }
      
      
      def solve_task4(
          air_data_path: str | Path = DEFAULT_AIR_DATA_PATH,
          radius_data_path: str | Path = DEFAULT_RADIUS_DATA_PATH,
          max_time_s: float = DEFAULT_MAX_TIME_S,
          time_step_s: float = TIME_STEP_S_DEFAULT,
          output_dt_s: float = OUTPUT_DT_S,
          n_intervals: int = N_DEFAULT,
          progress: bool = False,
      ) -> dict[str, Any]:
          """运行问题四基线求解，返回每60 s完整xi状态和精确终止状态。"""
      
          if max_time_s <= 0.0 or time_step_s <= 0.0 or output_dt_s <= 0.0:
              raise ValueError("最大时间、内部时间步和输出间隔必须为正")
          output_ratio = output_dt_s / time_step_s
          output_stride = int(round(output_ratio))
          if not np.isclose(output_ratio, output_stride, rtol=0.0, atol=1.0e-10):
              raise ValueError("输出间隔必须是内部时间步的整数倍")
          max_steps_float = max_time_s / time_step_s
          max_steps = int(round(max_steps_float))
          if not np.isclose(max_steps_float, max_steps, rtol=0.0, atol=1.0e-8):
              raise ValueError("最大时间必须是内部时间步的整数倍")
      
          air_time_s, air_temperature, air_moisture = load_air_data(air_data_path)
          radius_time_s, radius_values_m = load_radius_data(radius_data_path)
          if max_time_s > radius_time_s[-1] + 1.0e-10:
              raise ValueError(
                  f"请求求解至 {max_time_s:g}s，但附件2只覆盖到 {radius_time_s[-1]:g}s，"
                  "禁止无说明外推"
              )
          xi, faces, measure, dxi = fixed_xi_geometry(n_intervals)
          initial_temperature = np.full(xi.size, INITIAL_TEMPERATURE_C, dtype=float)
          initial_moisture = np.full(xi.size, INITIAL_MOISTURE_KGKG, dtype=float)
          current_temperature = initial_temperature.copy()
          current_moisture = initial_moisture.copy()
          current_time = 0.0
          current_radius = radius_at(current_time, radius_time_s, radius_values_m)
          current_max, _, _, _ = _max_info(current_moisture, xi, current_radius)
      
          sampled_times: list[float] = [0.0]
          sampled_radius_m: list[float] = [current_radius]
          sampled_temperature: list[np.ndarray] = [current_temperature.copy()]
          sampled_moisture: list[np.ndarray] = [current_moisture.copy()]
          sampled_max: list[float] = [current_max]
          iteration_counts: list[int] = []
          picard_delta_temperature: list[float] = []
          picard_delta_moisture: list[float] = []
          min_temperature = float(np.min(current_temperature))
          max_temperature = float(np.max(current_temperature))
          min_moisture = float(np.min(current_moisture))
          max_moisture = float(np.max(current_moisture))
          progress_next_time = 0.0
          termination: dict[str, Any] | None = None
      
          for step in range(1, max_steps + 1):
              time_new = min(float(step * time_step_s), float(max_time_s))
              dt_current = time_new - current_time
              if dt_current <= 0.0:
                  break
              radius_new = radius_at(time_new, radius_time_s, radius_values_m)
              temperature_new, moisture_new, iterations, delta_T, delta_C = _picard_step(
                  current_temperature,
                  current_moisture,
                  xi,
                  faces,
                  measure,
                  dxi,
                  current_radius,
                  radius_new,
                  dt_current,
                  _air_at(time_new, air_time_s, air_temperature),
                  _air_at(time_new, air_time_s, air_moisture),
              )
              iteration_counts.append(int(iterations))
              picard_delta_temperature.append(float(delta_T))
              picard_delta_moisture.append(float(delta_C))
              step_max, _, _, _ = _max_info(moisture_new, xi, radius_new)
              min_temperature = min(min_temperature, float(np.min(temperature_new)))
              max_temperature = max(max_temperature, float(np.max(temperature_new)))
              min_moisture = min(min_moisture, float(np.min(moisture_new)))
              max_moisture = max(max_moisture, float(np.max(moisture_new)))
      
              # 保留每60 s时刻的完整 xi 场，供后续绝对r和真实表面插值。
              if step % output_stride == 0:
                  sampled_times.append(float(time_new))
                  sampled_radius_m.append(float(radius_new))
                  sampled_temperature.append(temperature_new.copy())
                  sampled_moisture.append(moisture_new.copy())
                  sampled_max.append(float(step_max))
      
              if progress and (
                  step == 1 or time_new >= progress_next_time or time_new >= max_time_s
              ):
                  print(
                      f"  已推进 {time_new / 3600.0:.2f} h，R={radius_new * 100:.4f} cm，"
                      f"max C={step_max:.8f}，Picard={iterations}"
                  )
                  while progress_next_time <= time_new + 1.0e-10:
                      progress_next_time += 6.0 * 3600.0
      
              if step_max < DRYING_THRESHOLD_KGKG:
                  termination = _event_bisection(
                      current_time,
                      current_temperature,
                      current_moisture,
                      current_max,
                      time_new,
                      temperature_new,
                      moisture_new,
                      step_max,
                      xi,
                      faces,
                      measure,
                      dxi,
                      radius_time_s,
                      radius_values_m,
                      air_time_s,
                      air_temperature,
                      air_moisture,
                  )
                  break
      
              current_time = time_new
              current_radius = radius_new
              current_temperature = temperature_new
              current_moisture = moisture_new
              current_max = step_max
      
          if termination is None:
              raise RuntimeError(
                  f"在 {max_time_s / 3600.0:g} h 附件2覆盖范围内未达到全场严格阈值 "
                  f"max C < {DRYING_THRESHOLD_KGKG:g}"
              )
      
          result: dict[str, Any] = {
              "xi": xi,
              "dxi": float(dxi),
              "time_step_s": float(time_step_s),
              "output_dt_s": float(output_dt_s),
              "n_intervals": int(n_intervals),
              "radius_data_time_s": radius_time_s.copy(),
              "radius_data_m": radius_values_m.copy(),
              "air_data_time_s": air_time_s.copy(),
              "air_temperature_C": air_temperature.copy(),
              "air_moisture_kgkg": air_moisture.copy(),
              "sampled_times_s": np.asarray(sampled_times, dtype=float),
              "sampled_radius_m": np.asarray(sampled_radius_m, dtype=float),
              "sampled_temperature_internal_C": np.asarray(sampled_temperature, dtype=float),
              "sampled_moisture_internal_kgkg": np.asarray(sampled_moisture, dtype=float),
              "sampled_max_kgkg": np.asarray(sampled_max, dtype=float),
              "iteration_counts": np.asarray(iteration_counts, dtype=int),
              "picard_delta_temperature": np.asarray(picard_delta_temperature, dtype=float),
              "picard_delta_moisture": np.asarray(picard_delta_moisture, dtype=float),
              "min_temperature_C": float(min_temperature),
              "max_temperature_C": float(max_temperature),
              "min_internal_moisture_kgkg": float(min_moisture),
              "max_internal_moisture_kgkg": float(max_moisture),
          }
          result.update(termination)
          return result
      
      
      def validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
          """检查输入半径、离散边界、物性单位、采样和终止阈值。"""
      
          xi = np.asarray(solution["xi"], dtype=float)
          radius_data_time_s = np.asarray(solution["radius_data_time_s"], dtype=float)
          radius_data_m = np.asarray(solution["radius_data_m"], dtype=float)
          sampled_times = np.asarray(solution["sampled_times_s"], dtype=float)
          sampled_radius = np.asarray(solution["sampled_radius_m"], dtype=float)
          sampled_temperature = np.asarray(
              solution["sampled_temperature_internal_C"], dtype=float
          )
          sampled_moisture = np.asarray(
              solution["sampled_moisture_internal_kgkg"], dtype=float
          )
          termination_temperature = np.asarray(
              solution["termination_temperature_internal_C"], dtype=float
          )
          termination_moisture = np.asarray(
              solution["termination_moisture_internal_kgkg"], dtype=float
          )
          lower_temperature = np.asarray(
              solution["termination_lower_temperature_internal_C"], dtype=float
          )
          lower_moisture = np.asarray(
              solution["termination_lower_moisture_internal_kgkg"], dtype=float
          )
          all_arrays = (
              xi,
              radius_data_time_s,
              radius_data_m,
              sampled_times,
              sampled_radius,
              sampled_temperature,
              sampled_moisture,
              termination_temperature,
              termination_moisture,
              lower_temperature,
              lower_moisture,
          )
          if not all(np.all(np.isfinite(array)) for array in all_arrays):
              raise ValueError("问题四结果包含 NaN 或 Inf")
          if xi.ndim != 1 or xi.size < 3 or not np.isclose(xi[0], 0.0) or not np.isclose(xi[-1], 1.0):
              raise ValueError("固定xi网格端点错误")
          if np.any(np.diff(xi) <= 0.0):
              raise ValueError("固定xi网格不是严格递增")
          if not np.isclose(radius_data_m[0], RADIUS_INITIAL_M, atol=1.0e-12):
              raise ValueError("附件2初始半径读取错误")
          if np.any(np.diff(radius_data_m) > 1.0e-12):
              raise ValueError("附件2半径不是单调不增")
          if not np.isclose(sampled_times[0], 0.0, atol=1.0e-12):
              raise ValueError("60 s采样未从0 s开始")
          if sampled_times.size > 1 and not np.allclose(
              np.diff(sampled_times), OUTPUT_DT_S, rtol=0.0, atol=1.0e-8
          ):
              raise ValueError("60 s采样时间间隔错误")
          if sampled_temperature.shape != (sampled_times.size, xi.size):
              raise ValueError("每60 s温度完整xi状态形状错误")
          if sampled_moisture.shape != sampled_temperature.shape:
              raise ValueError("每60 s温度/水分完整xi状态形状不一致")
          if sampled_radius.shape != sampled_times.shape:
              raise ValueError("每60 s半径状态形状错误")
          expected_radius = np.array(
              [radius_at(t, radius_data_time_s, radius_data_m) for t in sampled_times]
          )
          if not np.allclose(sampled_radius, expected_radius, rtol=0.0, atol=1.0e-12):
              raise ValueError("每60 s半径没有使用附件2分段线性 R(t)")
          if np.min(sampled_moisture) < -1.0e-10 or np.min(termination_moisture) < -1.0e-10:
              raise ValueError("水分场出现明显负值")
          if termination_temperature.shape != xi.shape or termination_moisture.shape != xi.shape:
              raise ValueError("终止状态不是完整xi网格")
          if lower_temperature.shape != xi.shape or lower_moisture.shape != xi.shape:
              raise ValueError("终止下端状态不是完整xi网格")
      
          # 附件2已知数据点必须被原样读取；半径单位检查同时覆盖 cm->m。
          known_indices = np.unique(
              np.array([0, radius_data_time_s.size // 2, radius_data_time_s.size - 1])
          )
          known_radius_error = 0.0
          for index in known_indices:
              interpolated = radius_at(
                  radius_data_time_s[index], radius_data_time_s, radius_data_m
              )
              known_radius_error = max(
                  known_radius_error, abs(interpolated - radius_data_m[index])
              )
          if known_radius_error > 1.0e-14:
              raise ValueError("附件2已知时间点半径插值不一致")
      
          # 用一个独立计算的 Kelvin 表达式检查物性温度单位没有误用摄氏度。
          reference_T = np.array([50.0])
          reference_C = np.array([0.10])
          _, _, _, computed_D = material_properties(reference_T, reference_C)
          expected_D = 4.2e-4 * np.exp(-0.30 / 0.10) * np.exp(-3850.0 / (50.0 + 273.15))
          if not np.isclose(computed_D[0], expected_D, rtol=1.0e-13, atol=0.0):
              raise ValueError("D 的 Kelvin 温度验证失败")
      
          lower_max = float(solution["termination_lower_max_kgkg"])
          upper_max = float(solution["termination_max_kgkg"])
          lower_time = float(solution["termination_lower_time_s"])
          upper_time = float(solution["termination_time_s"])
          if not lower_max >= DRYING_THRESHOLD_KGKG:
              raise ValueError("终止括号下端已低于阈值")
          if not upper_max < DRYING_THRESHOLD_KGKG:
              raise ValueError("终止状态没有严格低于阈值")
          if not (lower_time < upper_time and upper_time - lower_time <= EVENT_TOL_S + 1.0e-10):
              raise ValueError("终止时刻括号不满足二分精度")
          if not np.isclose(lower_max, np.max(lower_moisture), atol=1.0e-12, rtol=0.0):
              raise ValueError("终止下端 max C 不是全xi场最大值")
          if not np.isclose(upper_max, np.max(termination_moisture), atol=1.0e-12, rtol=0.0):
              raise ValueError("终止上端 max C 不是全xi场最大值")
          upper_index = int(np.argmax(termination_moisture))
          if upper_index != int(solution["termination_max_index"]):
              raise ValueError("终止 max C 位置记录不一致")
          expected_upper_position = xi[upper_index] * float(solution["termination_radius_m"])
          if not np.isclose(
              expected_upper_position,
              float(solution["termination_max_radius_m"]),
              atol=1.0e-14,
              rtol=0.0,
          ):
              raise ValueError("终止 max C 的物理半径位置记录不一致")
      
          # 中心离散语义：xi=0，advection=b*xi/dxi=0，左侧扩散通量为空。
          if not np.isclose(xi[0], 0.0, atol=1.0e-14):
              raise ValueError("中心xi不是0")
          center_boundary_ok = True
      
          return {
              "termination_time_s": upper_time,
              "termination_time_h": upper_time / 3600.0,
              "termination_radius_cm": float(solution["termination_radius_m"]) * 100.0,
              "termination_max_kgkg": upper_max,
              "termination_max_xi": float(solution["termination_max_xi"]),
              "termination_max_radius_cm": float(solution["termination_max_radius_m"]) * 100.0,
              "termination_lower_time_s": lower_time,
              "termination_lower_max_kgkg": lower_max,
              "termination_bracket_width_s": upper_time - lower_time,
              "radius_known_point_max_error_m": known_radius_error,
              "temperature_min_C": float(solution["min_temperature_C"]),
              "temperature_max_C": float(solution["max_temperature_C"]),
              "moisture_min_kgkg": float(solution["min_internal_moisture_kgkg"]),
              "moisture_max_kgkg": float(solution["max_internal_moisture_kgkg"]),
              "max_picard_iterations": int(np.max(solution["iteration_counts"])),
              "mean_picard_iterations": float(np.mean(solution["iteration_counts"])),
              "sample_count": int(sampled_times.size),
              "internal_node_count": int(xi.size),
              "center_boundary_zero_flux_and_zero_advection": center_boundary_ok,
              "kelvin_reference_D_m2_s": float(computed_D[0]),
          }
      
      
      def run_sensitivity(
          air_data_path: str | Path = DEFAULT_AIR_DATA_PATH,
          radius_data_path: str | Path = DEFAULT_RADIUS_DATA_PATH,
          max_time_s: float = DEFAULT_MAX_TIME_S,
          progress: bool = False,
      ) -> dict[str, Any]:
          """接口：N=320、dt=0.5 s 的低成本加密复算。"""
      
          solution = solve_task4(
              air_data_path=air_data_path,
              radius_data_path=radius_data_path,
              max_time_s=max_time_s,
              time_step_s=0.5,
              output_dt_s=OUTPUT_DT_S,
              n_intervals=320,
              progress=progress,
          )
          return validate_solution(solution)
      
      
      def main() -> None:
          parser = argparse.ArgumentParser(description="求解A题问题四移动边界模型")
          parser.add_argument("--air-data-path", type=Path, default=DEFAULT_AIR_DATA_PATH)
          parser.add_argument("--radius-data-path", type=Path, default=DEFAULT_RADIUS_DATA_PATH)
          parser.add_argument("--max-time", type=float, default=DEFAULT_MAX_TIME_S)
          parser.add_argument("--time-step", type=float, default=TIME_STEP_S_DEFAULT)
          parser.add_argument("--output-dt", type=float, default=OUTPUT_DT_S)
          parser.add_argument("--n", type=int, default=N_DEFAULT)
          parser.add_argument("--no-write", action="store_true", help="本阶段不生成答案文件")
          parser.add_argument(
              "--skip-sensitivity",
              action="store_true",
              help="跳过 N=320、dt=0.5 s 的加密敏感性计算",
          )
          parser.add_argument("--progress", action="store_true", help="按6 h打印推进进度")
          args = parser.parse_args()
      
          started = wall_time.perf_counter()
          print(
              "问题四求解开始: "
              f"N={args.n}, dxi={1.0 / args.n:g}, dt={args.time_step:g}s, "
              f"output_dt={args.output_dt:g}s, threshold C<{DRYING_THRESHOLD_KGKG:g}"
          )
          solution = solve_task4(
              air_data_path=args.air_data_path,
              radius_data_path=args.radius_data_path,
              max_time_s=args.max_time,
              time_step_s=args.time_step,
              output_dt_s=args.output_dt,
              n_intervals=args.n,
              progress=args.progress,
          )
          summary = validate_solution(solution)
          print(f"基线数值检查: {summary}")
          print(
              "终止证据: "
              f"lower t={summary['termination_lower_time_s']:.6f}s "
              f"max C={summary['termination_lower_max_kgkg']:.8f}; "
              f"upper t={summary['termination_time_s']:.6f}s "
              f"max C={summary['termination_max_kgkg']:.8f}; "
              f"R={summary['termination_radius_cm']:.6f}cm, "
              f"max位置 r={summary['termination_max_radius_cm']:.6f}cm "
              f"(xi={summary['termination_max_xi']:.6f})"
          )
          if not args.skip_sensitivity:
              sensitivity_started = wall_time.perf_counter()
              sensitivity_summary = run_sensitivity(
                  air_data_path=args.air_data_path,
                  radius_data_path=args.radius_data_path,
                  max_time_s=args.max_time,
                  progress=args.progress,
              )
              print(f"N=320, dt=0.5s 敏感性检查: {sensitivity_summary}")
              print(
                  f"敏感性计算耗时: {wall_time.perf_counter() - sensitivity_started:.2f}s"
              )
          if args.no_write:
              print("--no-write: 本阶段未生成任何 answer 文件")
          print(f"总耗时: {wall_time.perf_counter() - started:.2f}s")
      
      
      if __name__ == "__main__":
          main()

## Activity

    Completed `/root/task4_solver`

## Activity

    agent tool: Wait · Completed

## Activity

    $ /bin/zsh -lc 'git show --stat --oneline bbc9c4f && git show --name-status --format=fuller bbc9c4f && git status --short --branch && git diff --check && git diff --cached --name-status && rg -n "harmonic|_event_bisection|radius_rate|boundary_conductance|N_DEFAULT|TIME_STEP" solution/task4/script/solve_task4.py'
    status: Completed · exit 0
      bbc9c4f 建立问题四移动边界求解器
       solution/task4/script/solve_task4.py | 899 +++++++++++++++++++++++++++++++++++
       1 file changed, 899 insertions(+)
      commit bbc9c4f7c59587add316b27e43894b77bb01316d
      Author:     chixin114514 <jiaqiaosu114514@outlook.com>
      AuthorDate: Fri Sep 11 00:28:59 2026 +0800
      Commit:     chixin114514 <jiaqiaosu114514@outlook.com>
      CommitDate: Fri Sep 11 00:28:59 2026 +0800
      
          建立问题四移动边界求解器
      
      A	solution/task4/script/solve_task4.py
      ## main...origin/main [ahead 1]
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/
      37:N_DEFAULT = 160  # xi 区间数，dxi=1/160
      38:TIME_STEP_S_DEFAULT = 1.0
      179:def _harmonic_mean(left: np.ndarray, right: np.ndarray) -> np.ndarray:
      214:    radius_rate_m_s: float,
      224:    face_conductivity = _harmonic_mean(conductivity[:-1], conductivity[1:])
      227:    b = -radius_rate_m_s / radius_m
      253:    boundary_conductance = HEAT_TRANSFER_W_M2_K / radius_m
      254:    diagonal[-1] += dt_s * (conductance[-1] + boundary_conductance)
      256:    rhs[-1] += dt_s * boundary_conductance * air_temperature_C
      269:    radius_rate_m_s: float,
      279:    face_diffusivity = _harmonic_mean(diffusivity[:-1], diffusivity[1:])
      281:    b = -radius_rate_m_s / radius_m
      302:    boundary_conductance = MASS_TRANSFER_M_S / radius_m
      303:    diagonal[-1] += dt_s * (conductance[-1] + boundary_conductance)
      305:    rhs[-1] += dt_s * boundary_conductance * air_moisture_kgkg
      326:    radius_rate_m_s = (radius_new_m - radius_old_m) / dt_s
      342:            radius_rate_m_s,
      358:            radius_rate_m_s,
      407:def _event_bisection(
      509:    time_step_s: float = TIME_STEP_S_DEFAULT,
      511:    n_intervals: int = N_DEFAULT,
      605:            termination = _event_bisection(
      842:    parser.add_argument("--time-step", type=float, default=TIME_STEP_S_DEFAULT)
      844:    parser.add_argument("--n", type=int, default=N_DEFAULT)

## Assistant

首轮验收未通过，发现两项需要定向修正：

1. 脚本把界面 \(k,D\) 改成了调和平均，但当前已验证的 task2/task3 实现使用算术平均；题目要求除问题四指定变化外不改基线，这一处必须恢复。
2. 当前事件二分在更新下端后，又从“新下端状态”继续积分，而上端仍来自旧时间分割，导致二分函数不是同一个一致的时间离散映射。应始终从首次跨阈值前的固定状态，分别积分到候选时刻。

此外，最终结果将采用 `N=320, dt=0.5 s` 加密解；`N=160, dt=1 s` 只作为敏感性对照。修正后必须重跑两组，因为界面平均方式会改变数值。

## Activity

    Interacted with `/root/task4_solver`

## Activity

    agent tool: Wait · Completed

## Assistant

修正版本正在重算两组网格。首轮的 `52.5046 h / 52.4076 h` 只能视为被否决实现的诊断值，不会进入最终答案。下一检查点是确认算术平均恢复后，终止时间差是否仍处于约 0.2% 的量级，并审查事件括号确实来自同一个离散时间映射。

## Activity

    Completed `/root/task4_solver`

## Activity

    agent tool: Wait · Completed

## Activity

    $ /bin/zsh -lc "git show --stat --oneline 07cf885 && git show --format= -- solution/task4/script/solve_task4.py | sed -n '1,360p' && sed -n '165,330p' solution/task4/script/solve_task4.py && sed -n '395,510p' solution/task4/script/solve_task4.py && sed -n '780,900p' solution/task4/script/solve_task4.py && git status --short --branch"
    status: Completed · exit 0
      07cf885 修正问题四界面离散与终止事件定位
       solution/task4/script/solve_task4.py | 78 +++++++++++++++++++++---------------
       1 file changed, 46 insertions(+), 32 deletions(-)
      diff --git a/solution/task4/script/solve_task4.py b/solution/task4/script/solve_task4.py
      index 3b17855..a39a990 100644
      --- a/solution/task4/script/solve_task4.py
      +++ b/solution/task4/script/solve_task4.py
      @@ -33,9 +33,9 @@ INITIAL_MOISTURE_KGKG = 2.55
       HEAT_TRANSFER_W_M2_K = 25.0
       MASS_TRANSFER_M_S = 8.0e-7
      
      -# 问题四数值默认值。
      -N_DEFAULT = 160  # xi 区间数，dxi=1/160
      -TIME_STEP_S_DEFAULT = 1.0
      +# 问题四数值默认值：最终结果采用加密网格；粗解仅作为对照。
      +N_DEFAULT = 320  # xi 区间数，dxi=1/320
      +TIME_STEP_S_DEFAULT = 0.5
       OUTPUT_DT_S = 60.0
       DRYING_THRESHOLD_KGKG = 0.15
       EVENT_TOL_S = 1.0e-3
      @@ -176,13 +176,6 @@ def material_properties(
           return rho, cp, conductivity, diffusivity
      
      
      -def _harmonic_mean(left: np.ndarray, right: np.ndarray) -> np.ndarray:
      -    denominator = left + right
      -    if np.any(denominator <= 0.0):
      -        raise ValueError("界面物性必须为正")
      -    return 2.0 * left * right / denominator
      -
      -
       def _solve_tridiagonal(
           lower: np.ndarray,
           diagonal: np.ndarray,
      @@ -221,7 +214,9 @@ def _assemble_temperature_system(
               guess_temperature_C, guess_moisture_kgkg
           )
           storage = rho * cp * measure
      -    face_conductivity = _harmonic_mean(conductivity[:-1], conductivity[1:])
      +    # 继承 task2/task3 实际求解器的界面物性算术平均；问题四只改变
      +    # 题目指定的物性公式和移动边界，不额外改变固定边界模型的界面离散。
      +    face_conductivity = 0.5 * (conductivity[:-1] + conductivity[1:])
           # 固定xi控制体扩散导通量：1/R^2 * xi_face*k_face/dxi。
           conductance = face_conductivity * faces / (radius_m**2 * dxi)
           b = -radius_rate_m_s / radius_m
      @@ -276,7 +271,8 @@ def _assemble_moisture_system(
               guess_temperature_C, guess_moisture_kgkg
           )
           storage = measure.copy()
      -    face_diffusivity = _harmonic_mean(diffusivity[:-1], diffusivity[1:])
      +    # 同 task2/task3，界面扩散系数使用算术平均。
      +    face_diffusivity = 0.5 * (diffusivity[:-1] + diffusivity[1:])
           conductance = face_diffusivity * faces / (radius_m**2 * dxi)
           b = -radius_rate_m_s / radius_m
           if b < -1.0e-12:
      @@ -423,16 +419,31 @@ def _event_bisection(
           air_temperature_C: np.ndarray,
           air_moisture_kgkg: np.ndarray,
       ) -> dict[str, Any]:
      -    """首次跨阈值后，用同一前一状态的局部时间段二分终止时刻。"""
      +    """首次跨阈值后，从固定 base 状态二分终止时刻。
      +
      +    每个候选时刻都计算统一函数
      +
      +        F(t) = max_xi C(t; base_state -> t) - 0.15,
      +
      +    其中 ``base_state`` 是首次跨阈值时间步前的状态。lower/upper 只更新
      +    候选时刻及其由 base_state 直接积分得到的状态，不能把更新后的 lower
      +    状态作为下一次候选的起点。
      +    """
      
           if not (lower_max_kgkg >= DRYING_THRESHOLD_KGKG):
               raise ValueError("事件二分下端不在阈值上方")
           if not (upper_max_kgkg < DRYING_THRESHOLD_KGKG):
               raise ValueError("事件二分上端未严格低于阈值")
      -    lower_time = float(lower_time_s)
      +    # 固定首次跨阈值前的 base 状态；所有候选都从它重新推进。
      +    base_time = float(lower_time_s)
      +    base_temperature = lower_temperature_C.copy()
      +    base_moisture = lower_moisture_kgkg.copy()
      +    base_radius = radius_at(base_time, radius_time_s, radius_m)
      +
      +    lower_time = base_time
           upper_time = float(upper_time_s)
      -    lower_temperature = lower_temperature_C.copy()
      -    lower_moisture = lower_moisture_kgkg.copy()
      +    lower_temperature = base_temperature.copy()
      +    lower_moisture = base_moisture.copy()
           lower_max = float(lower_max_kgkg)
           upper_temperature = upper_temperature_C.copy()
           upper_moisture = upper_moisture_kgkg.copy()
      @@ -441,17 +452,16 @@ def _event_bisection(
           while upper_time - lower_time > EVENT_TOL_S:
               midpoint = 0.5 * (lower_time + upper_time)
               midpoint_radius = radius_at(midpoint, radius_time_s, radius_m)
      -        old_radius = radius_at(lower_time, radius_time_s, radius_m)
               midpoint_temperature, midpoint_moisture, _, _, _ = _picard_step(
      -            lower_temperature,
      -            lower_moisture,
      +            base_temperature,
      +            base_moisture,
                   xi,
                   faces,
                   measure,
                   dxi,
      -            old_radius,
      +            base_radius,
                   midpoint_radius,
      -            midpoint - lower_time,
      +            midpoint - base_time,
                   _air_at(midpoint, air_time_s, air_temperature_C),
                   _air_at(midpoint, air_time_s, air_moisture_kgkg),
               )
      @@ -814,21 +824,21 @@ def validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
           }
      
      
      -def run_sensitivity(
      +def run_coarse_comparison(
           air_data_path: str | Path = DEFAULT_AIR_DATA_PATH,
           radius_data_path: str | Path = DEFAULT_RADIUS_DATA_PATH,
           max_time_s: float = DEFAULT_MAX_TIME_S,
           progress: bool = False,
       ) -> dict[str, Any]:
      -    """接口：N=320、dt=0.5 s 的低成本加密复算。"""
      +    """运行 N=160、dt=1 s 的粗网格对照解。"""
      
           solution = solve_task4(
               air_data_path=air_data_path,
               radius_data_path=radius_data_path,
               max_time_s=max_time_s,
      -        time_step_s=0.5,
      +        time_step_s=1.0,
               output_dt_s=OUTPUT_DT_S,
      -        n_intervals=320,
      +        n_intervals=160,
               progress=progress,
           )
           return validate_solution(solution)
      @@ -846,14 +856,14 @@ def main() -> None:
           parser.add_argument(
               "--skip-sensitivity",
               action="store_true",
      -        help="跳过 N=320、dt=0.5 s 的加密敏感性计算",
      +        help="跳过 N=160、dt=1 s 的粗网格对照计算",
           )
           parser.add_argument("--progress", action="store_true", help="按6 h打印推进进度")
           args = parser.parse_args()
      
           started = wall_time.perf_counter()
           print(
      -        "问题四求解开始: "
      +        "问题四最终加密解开始: "
               f"N={args.n}, dxi={1.0 / args.n:g}, dt={args.time_step:g}s, "
               f"output_dt={args.output_dt:g}s, threshold C<{DRYING_THRESHOLD_KGKG:g}"
           )
      @@ -867,7 +877,7 @@ def main() -> None:
               progress=args.progress,
           )
           summary = validate_solution(solution)
      -    print(f"基线数值检查: {summary}")
      +    print(f"最终加密解数值检查: {summary}")
           print(
               "终止证据: "
               f"lower t={summary['termination_lower_time_s']:.6f}s "
      @@ -879,16 +889,20 @@ def main() -> None:
               f"(xi={summary['termination_max_xi']:.6f})"
           )
           if not args.skip_sensitivity:
      -        sensitivity_started = wall_time.perf_counter()
      -        sensitivity_summary = run_sensitivity(
      +        coarse_started = wall_time.perf_counter()
      +        coarse_summary = run_coarse_comparison(
                   air_data_path=args.air_data_path,
                   radius_data_path=args.radius_data_path,
                   max_time_s=args.max_time,
                   progress=args.progress,
               )
      -        print(f"N=320, dt=0.5s 敏感性检查: {sensitivity_summary}")
      +        print(f"N=160, dt=1s 粗网格对照: {coarse_summary}")
      +        print(
      +            f"结束时间差（加密-粗解）: "
      +            f"{summary['termination_time_h'] - coarse_summary['termination_time_h']:.8f} h"
      +        )
               print(
      -            f"敏感性计算耗时: {wall_time.perf_counter() - sensitivity_started:.2f}s"
      +            f"粗网格对照耗时: {wall_time.perf_counter() - coarse_started:.2f}s"
               )
           if args.no_write:
               print("--no-write: 本阶段未生成任何 answer 文件")
          concentration = np.maximum(moisture_kgkg, 1.0e-12)
          temperature_K = temperature_C + 273.15
          if np.any(~np.isfinite(temperature_K)) or np.any(temperature_K <= 0.0):
              raise ValueError("附录4物性计算遇到非正或非有限 Kelvin 温度")
      
          rho = 760.0 + 90.0 * concentration
          cp = 1850.0 + 2150.0 * concentration / (concentration + 1.0)
          conductivity = 0.12 + 0.20 * concentration / (concentration + 1.0)
          diffusivity = 4.2e-4 * np.exp(-0.30 / concentration) * np.exp(
              -3850.0 / temperature_K
          )
          return rho, cp, conductivity, diffusivity
      
      
      def _solve_tridiagonal(
          lower: np.ndarray,
          diagonal: np.ndarray,
          upper: np.ndarray,
          rhs: np.ndarray,
      ) -> np.ndarray:
          """解三对角系统；输入 lower/upper 长度为 n-1。"""
      
          n = diagonal.size
          banded = np.zeros((3, n), dtype=float)
          banded[0, 1:] = upper
          banded[1, :] = diagonal
          banded[2, :-1] = lower
          solution = solve_banded((1, 1), banded, rhs, check_finite=False)
          if not np.all(np.isfinite(solution)):
              raise RuntimeError("三对角线性系统求解得到 NaN 或 Inf")
          return solution
      
      
      def _assemble_temperature_system(
          old_temperature_C: np.ndarray,
          guess_temperature_C: np.ndarray,
          guess_moisture_kgkg: np.ndarray,
          xi: np.ndarray,
          faces: np.ndarray,
          measure: np.ndarray,
          dxi: float,
          radius_m: float,
          radius_rate_m_s: float,
          dt_s: float,
          air_temperature_C: float,
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
          """组装固定xi坐标下的温度后向欧拉矩阵。"""
      
          rho, cp, conductivity, _ = material_properties(
              guess_temperature_C, guess_moisture_kgkg
          )
          storage = rho * cp * measure
          # 继承 task2/task3 实际求解器的界面物性算术平均；问题四只改变
          # 题目指定的物性公式和移动边界，不额外改变固定边界模型的界面离散。
          face_conductivity = 0.5 * (conductivity[:-1] + conductivity[1:])
          # 固定xi控制体扩散导通量：1/R^2 * xi_face*k_face/dxi。
          conductance = face_conductivity * faces / (radius_m**2 * dxi)
          b = -radius_rate_m_s / radius_m
          if b < -1.0e-12:
              raise ValueError("R(t)出现膨胀，不能继续使用 b>=0 的后向迎风差分")
          b = max(0.0, b)
          # PDE 的移动项为 b*xi*T_xi，b>=0 时使用 (T_j-T_{j-1})/dxi。
          advection = storage * b * xi / dxi
      
          diagonal = storage.copy()
          lower = np.zeros(storage.size - 1, dtype=float)
          upper = np.zeros(storage.size - 1, dtype=float)
          rhs = storage * old_temperature_C
          diagonal += dt_s * advection
          lower -= dt_s * advection[1:]
      
          # 中心自然零通量；中心项没有左邻接、没有移动项（xi=0）。
          diagonal[0] += dt_s * conductance[0]
          upper[0] -= dt_s * conductance[0]
          # 内部控制体。
          if storage.size > 2:
              left = conductance[:-1]
              right = conductance[1:]
              diagonal[1:-1] += dt_s * (left + right)
              # row j=1..n-2 的下/上三对角项分别对应 g_{j-1}/g_j。
              lower[:-1] -= dt_s * left
              upper[1:] -= dt_s * right
          # 移动表面 Robin：-(k/R)T_xi=h(Ts-Tair)，换成 h/R 的边界导通量。
          boundary_conductance = HEAT_TRANSFER_W_M2_K / radius_m
          diagonal[-1] += dt_s * (conductance[-1] + boundary_conductance)
          lower[-1] -= dt_s * conductance[-1]
          rhs[-1] += dt_s * boundary_conductance * air_temperature_C
          return lower, diagonal, upper, rhs
      
      
      def _assemble_moisture_system(
          old_moisture_kgkg: np.ndarray,
          guess_temperature_C: np.ndarray,
          guess_moisture_kgkg: np.ndarray,
          xi: np.ndarray,
          faces: np.ndarray,
          measure: np.ndarray,
          dxi: float,
          radius_m: float,
          radius_rate_m_s: float,
          dt_s: float,
          air_moisture_kgkg: float,
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
          """组装固定xi坐标下的水分后向欧拉矩阵。"""
      
          _, _, _, diffusivity = material_properties(
              guess_temperature_C, guess_moisture_kgkg
          )
          storage = measure.copy()
          # 同 task2/task3，界面扩散系数使用算术平均。
          face_diffusivity = 0.5 * (diffusivity[:-1] + diffusivity[1:])
          conductance = face_diffusivity * faces / (radius_m**2 * dxi)
          b = -radius_rate_m_s / radius_m
          if b < -1.0e-12:
              raise ValueError("R(t)出现膨胀，不能继续使用 b>=0 的后向迎风差分")
          b = max(0.0, b)
          advection = storage * b * xi / dxi
      
          diagonal = storage.copy()
          lower = np.zeros(storage.size - 1, dtype=float)
          upper = np.zeros(storage.size - 1, dtype=float)
          rhs = storage * old_moisture_kgkg
          diagonal += dt_s * advection
          lower -= dt_s * advection[1:]
      
          diagonal[0] += dt_s * conductance[0]
          upper[0] -= dt_s * conductance[0]
          if storage.size > 2:
              left = conductance[:-1]
              right = conductance[1:]
              diagonal[1:-1] += dt_s * (left + right)
              lower[:-1] -= dt_s * left
              upper[1:] -= dt_s * right
          boundary_conductance = MASS_TRANSFER_M_S / radius_m
          diagonal[-1] += dt_s * (conductance[-1] + boundary_conductance)
          lower[-1] -= dt_s * conductance[-1]
          rhs[-1] += dt_s * boundary_conductance * air_moisture_kgkg
          return lower, diagonal, upper, rhs
      
      
      def _picard_step(
          old_temperature_C: np.ndarray,
          old_moisture_kgkg: np.ndarray,
          xi: np.ndarray,
          faces: np.ndarray,
          measure: np.ndarray,
          dxi: float,
          radius_old_m: float,
          radius_new_m: float,
          dt_s: float,
          air_temperature_C: float,
          air_moisture_kgkg: float,
      ) -> tuple[np.ndarray, np.ndarray, int, float, float]:
          """一个移动边界时间步内的 Picard 热湿耦合迭代。"""
      
          if dt_s <= 0.0:
              raise ValueError("Picard 时间步必须为正")
          radius_rate_m_s = (radius_new_m - radius_old_m) / dt_s
          guess_temperature_C = old_temperature_C.copy()
          guess_moisture_kgkg = old_moisture_kgkg.copy()
          last_delta_temperature = np.inf
          last_delta_moisture = np.inf
      
          for iteration in range(1, PICARD_MAX_ITER + 1):
              lower_T, diagonal_T, upper_T, rhs_T = _assemble_temperature_system(
                  old_temperature_C,
      ) -> tuple[float, int, float, float]:
          index = int(np.argmax(moisture_kgkg))
          maximum = float(moisture_kgkg[index])
          xi_position = float(xi[index])
          radius_position_m = xi_position * radius_m
          return maximum, index, xi_position, radius_position_m
      
      
      def _event_bisection(
          lower_time_s: float,
          lower_temperature_C: np.ndarray,
          lower_moisture_kgkg: np.ndarray,
          lower_max_kgkg: float,
          upper_time_s: float,
          upper_temperature_C: np.ndarray,
          upper_moisture_kgkg: np.ndarray,
          upper_max_kgkg: float,
          xi: np.ndarray,
          faces: np.ndarray,
          measure: np.ndarray,
          dxi: float,
          radius_time_s: np.ndarray,
          radius_m: np.ndarray,
          air_time_s: np.ndarray,
          air_temperature_C: np.ndarray,
          air_moisture_kgkg: np.ndarray,
      ) -> dict[str, Any]:
          """首次跨阈值后，从固定 base 状态二分终止时刻。
      
          每个候选时刻都计算统一函数
      
              F(t) = max_xi C(t; base_state -> t) - 0.15,
      
          其中 ``base_state`` 是首次跨阈值时间步前的状态。lower/upper 只更新
          候选时刻及其由 base_state 直接积分得到的状态，不能把更新后的 lower
          状态作为下一次候选的起点。
          """
      
          if not (lower_max_kgkg >= DRYING_THRESHOLD_KGKG):
              raise ValueError("事件二分下端不在阈值上方")
          if not (upper_max_kgkg < DRYING_THRESHOLD_KGKG):
              raise ValueError("事件二分上端未严格低于阈值")
          # 固定首次跨阈值前的 base 状态；所有候选都从它重新推进。
          base_time = float(lower_time_s)
          base_temperature = lower_temperature_C.copy()
          base_moisture = lower_moisture_kgkg.copy()
          base_radius = radius_at(base_time, radius_time_s, radius_m)
      
          lower_time = base_time
          upper_time = float(upper_time_s)
          lower_temperature = base_temperature.copy()
          lower_moisture = base_moisture.copy()
          lower_max = float(lower_max_kgkg)
          upper_temperature = upper_temperature_C.copy()
          upper_moisture = upper_moisture_kgkg.copy()
          upper_max = float(upper_max_kgkg)
      
          while upper_time - lower_time > EVENT_TOL_S:
              midpoint = 0.5 * (lower_time + upper_time)
              midpoint_radius = radius_at(midpoint, radius_time_s, radius_m)
              midpoint_temperature, midpoint_moisture, _, _, _ = _picard_step(
                  base_temperature,
                  base_moisture,
                  xi,
                  faces,
                  measure,
                  dxi,
                  base_radius,
                  midpoint_radius,
                  midpoint - base_time,
                  _air_at(midpoint, air_time_s, air_temperature_C),
                  _air_at(midpoint, air_time_s, air_moisture_kgkg),
              )
              midpoint_max, _, _, _ = _max_info(
                  midpoint_moisture, xi, midpoint_radius
              )
              if midpoint_max < DRYING_THRESHOLD_KGKG:
                  upper_time = midpoint
                  upper_temperature = midpoint_temperature
                  upper_moisture = midpoint_moisture
                  upper_max = midpoint_max
              else:
                  lower_time = midpoint
                  lower_temperature = midpoint_temperature
                  lower_moisture = midpoint_moisture
                  lower_max = midpoint_max
      
          upper_radius = radius_at(upper_time, radius_time_s, radius_m)
          maximum, index, xi_position, radius_position_m = _max_info(
              upper_moisture, xi, upper_radius
          )
          lower_radius = radius_at(lower_time, radius_time_s, radius_m)
          lower_max_check, lower_index, lower_xi, lower_position_m = _max_info(
              lower_moisture, xi, lower_radius
          )
          if not np.isclose(maximum, upper_max, rtol=0.0, atol=1.0e-12):
              raise RuntimeError("事件二分上端最大值记录不一致")
          if not np.isclose(lower_max_check, lower_max, rtol=0.0, atol=1.0e-12):
              raise RuntimeError("事件二分下端最大值记录不一致")
          return {
              "termination_time_s": float(upper_time),
              "termination_temperature_internal_C": upper_temperature,
              "termination_moisture_internal_kgkg": upper_moisture,
              "termination_max_kgkg": float(maximum),
              "termination_max_index": int(index),
              "termination_max_xi": float(xi_position),
              "termination_max_radius_m": float(radius_position_m),
              "termination_radius_m": float(upper_radius),
              "termination_lower_time_s": float(lower_time),
              "termination_lower_temperature_internal_C": lower_temperature,
              "termination_lower_moisture_internal_kgkg": lower_moisture,
              "termination_lower_max_kgkg": float(lower_max_check),
              "termination_lower_max_index": int(lower_index),
              "termination_lower_max_xi": float(lower_xi),
              "termination_lower_max_radius_m": float(lower_position_m),
              "termination_lower_radius_m": float(lower_radius),
          if not (lower_time < upper_time and upper_time - lower_time <= EVENT_TOL_S + 1.0e-10):
              raise ValueError("终止时刻括号不满足二分精度")
          if not np.isclose(lower_max, np.max(lower_moisture), atol=1.0e-12, rtol=0.0):
              raise ValueError("终止下端 max C 不是全xi场最大值")
          if not np.isclose(upper_max, np.max(termination_moisture), atol=1.0e-12, rtol=0.0):
              raise ValueError("终止上端 max C 不是全xi场最大值")
          upper_index = int(np.argmax(termination_moisture))
          if upper_index != int(solution["termination_max_index"]):
              raise ValueError("终止 max C 位置记录不一致")
          expected_upper_position = xi[upper_index] * float(solution["termination_radius_m"])
          if not np.isclose(
              expected_upper_position,
              float(solution["termination_max_radius_m"]),
              atol=1.0e-14,
              rtol=0.0,
          ):
              raise ValueError("终止 max C 的物理半径位置记录不一致")
      
          # 中心离散语义：xi=0，advection=b*xi/dxi=0，左侧扩散通量为空。
          if not np.isclose(xi[0], 0.0, atol=1.0e-14):
              raise ValueError("中心xi不是0")
          center_boundary_ok = True
      
          return {
              "termination_time_s": upper_time,
              "termination_time_h": upper_time / 3600.0,
              "termination_radius_cm": float(solution["termination_radius_m"]) * 100.0,
              "termination_max_kgkg": upper_max,
              "termination_max_xi": float(solution["termination_max_xi"]),
              "termination_max_radius_cm": float(solution["termination_max_radius_m"]) * 100.0,
              "termination_lower_time_s": lower_time,
              "termination_lower_max_kgkg": lower_max,
              "termination_bracket_width_s": upper_time - lower_time,
              "radius_known_point_max_error_m": known_radius_error,
              "temperature_min_C": float(solution["min_temperature_C"]),
              "temperature_max_C": float(solution["max_temperature_C"]),
              "moisture_min_kgkg": float(solution["min_internal_moisture_kgkg"]),
              "moisture_max_kgkg": float(solution["max_internal_moisture_kgkg"]),
              "max_picard_iterations": int(np.max(solution["iteration_counts"])),
              "mean_picard_iterations": float(np.mean(solution["iteration_counts"])),
              "sample_count": int(sampled_times.size),
              "internal_node_count": int(xi.size),
              "center_boundary_zero_flux_and_zero_advection": center_boundary_ok,
              "kelvin_reference_D_m2_s": float(computed_D[0]),
          }
      
      
      def run_coarse_comparison(
          air_data_path: str | Path = DEFAULT_AIR_DATA_PATH,
          radius_data_path: str | Path = DEFAULT_RADIUS_DATA_PATH,
          max_time_s: float = DEFAULT_MAX_TIME_S,
          progress: bool = False,
      ) -> dict[str, Any]:
          """运行 N=160、dt=1 s 的粗网格对照解。"""
      
          solution = solve_task4(
              air_data_path=air_data_path,
              radius_data_path=radius_data_path,
              max_time_s=max_time_s,
              time_step_s=1.0,
              output_dt_s=OUTPUT_DT_S,
              n_intervals=160,
              progress=progress,
          )
          return validate_solution(solution)
      
      
      def main() -> None:
          parser = argparse.ArgumentParser(description="求解A题问题四移动边界模型")
          parser.add_argument("--air-data-path", type=Path, default=DEFAULT_AIR_DATA_PATH)
          parser.add_argument("--radius-data-path", type=Path, default=DEFAULT_RADIUS_DATA_PATH)
          parser.add_argument("--max-time", type=float, default=DEFAULT_MAX_TIME_S)
          parser.add_argument("--time-step", type=float, default=TIME_STEP_S_DEFAULT)
          parser.add_argument("--output-dt", type=float, default=OUTPUT_DT_S)
          parser.add_argument("--n", type=int, default=N_DEFAULT)
          parser.add_argument("--no-write", action="store_true", help="本阶段不生成答案文件")
          parser.add_argument(
              "--skip-sensitivity",
              action="store_true",
              help="跳过 N=160、dt=1 s 的粗网格对照计算",
          )
          parser.add_argument("--progress", action="store_true", help="按6 h打印推进进度")
          args = parser.parse_args()
      
          started = wall_time.perf_counter()
          print(
              "问题四最终加密解开始: "
              f"N={args.n}, dxi={1.0 / args.n:g}, dt={args.time_step:g}s, "
              f"output_dt={args.output_dt:g}s, threshold C<{DRYING_THRESHOLD_KGKG:g}"
          )
          solution = solve_task4(
              air_data_path=args.air_data_path,
              radius_data_path=args.radius_data_path,
              max_time_s=args.max_time,
              time_step_s=args.time_step,
              output_dt_s=args.output_dt,
              n_intervals=args.n,
              progress=args.progress,
          )
          summary = validate_solution(solution)
          print(f"最终加密解数值检查: {summary}")
          print(
              "终止证据: "
              f"lower t={summary['termination_lower_time_s']:.6f}s "
              f"max C={summary['termination_lower_max_kgkg']:.8f}; "
              f"upper t={summary['termination_time_s']:.6f}s "
              f"max C={summary['termination_max_kgkg']:.8f}; "
              f"R={summary['termination_radius_cm']:.6f}cm, "
              f"max位置 r={summary['termination_max_radius_cm']:.6f}cm "
              f"(xi={summary['termination_max_xi']:.6f})"
          )
          if not args.skip_sensitivity:
              coarse_started = wall_time.perf_counter()
              coarse_summary = run_coarse_comparison(
                  air_data_path=args.air_data_path,
                  radius_data_path=args.radius_data_path,
                  max_time_s=args.max_time,
                  progress=args.progress,
              )
              print(f"N=160, dt=1s 粗网格对照: {coarse_summary}")
              print(
      ## main...origin/main [ahead 2]
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/

## Assistant

第二轮验收通过：修正后最终加密解为 `52.3708637 h`，粗网格对照为 `52.3510623 h`，差 `0.0198014 h`（约 71.3 s，0.038%）。阈值上、下端间隔不足 `0.001 s`，最大值均位于中心。

现在进入结果文件阶段：`result4.xlsx` 将保留固定绝对位置 `0.0–2.0 cm`，超出当时 \(R(t)\) 的单元格留空，并额外设置“药材表面”列；论文表 6 采用从 6 h 起始仍有效的 `0、0.5、1.0 cm、药材表面`。CSV 同时保存 60 s 有效内部点、动态表面和精确结束状态。

## Activity

    Interacted with `/root/task4_solver`

## Activity

    agent tool: Wait · Completed

## Assistant

输出阶段仍在运行，主要耗时是重新生成最终加密解并逐点回读约数万条记录。完成后不会只检查文件“能打开”，还会验证：

- XLSX 固定位置越界单元格确实为空；
- 表面列始终对应 \(\xi=1\)；
- CSV 与 XLSX 的四位小数逐点一致；
- 精确结束状态没有被误塞进 60 s 官方输出网格；
- 表 6 结束行使用真实表面 `r=1.2 cm`。

## Activity

    agent tool: Wait · Completed

## Activity

    agent tool: Wait · Completed

## Activity

    $ /bin/zsh -lc "git status --short --branch && git log --oneline -n 6 && find solution/task4 -maxdepth 3 -type f -print -exec ls -lh {} \\; && rg -n \"write_result|paper|csv|validate_written|iter_rows|worksheet.cell\" solution/task4/script/solve_task4.py | tail -80"
    status: Completed · exit 0
      ## main...origin/main [ahead 3]
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/
      c4bc983 实现问题四结果文件生成与验收
      07cf885 修正问题四界面离散与终止事件定位
      bbc9c4f 建立问题四移动边界求解器
      4040291 补充任务三交接文档
      b5eb0bb 补充问题二与问题三交接文档
      735fbbd 生成问题三完整结果文件并通过验证
      solution/task4/script/solve_task4.py
      -rw-r--r--@ 1 jiaqiaosu  staff    67K Sep 11 00:50 solution/task4/script/solve_task4.py
      59:DEFAULT_CSV_PATH = DEFAULT_ANSWER_DIR / "task4_all_answers.csv"
      861:def _paper_regular_hours(solution: dict[str, Any]) -> list[int]:
      905:def write_result_xlsx(
      918:    header_style = copy(worksheet.cell(row=1, column=2)._style)
      919:    time_style = copy(worksheet.cell(row=2, column=1)._style)
      920:    value_style = copy(worksheet.cell(row=2, column=2)._style)
      925:    worksheet.cell(row=1, column=1).value = "时间\\到药材中心的距离"
      927:        cell = worksheet.cell(row=1, column=column_index, value=float(radius_cm))
      930:    surface_header = worksheet.cell(row=1, column=OUTPUT_RADIUS_CM.size + 2, value="药材表面")
      944:        time_cell = worksheet.cell(row=row_index, column=1, value=int(round(sampled_times[state_index])))
      956:            cell = worksheet.cell(row=row_index, column=column_index)
      964:        surface_cell = worksheet.cell(
      972:def _csv_state_rows(
      1030:def write_result_csv(
      1050:            _csv_state_rows(
      1061:        _csv_state_rows(
      1072:        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
      1077:def _paper_rows(solution: dict[str, Any]) -> list[list[Any]]:
      1089:    for hour in _paper_regular_hours(solution):
      1135:def write_paper_table(
      1147:        cell = worksheet.cell(row=1, column=column_index, value=header)
      1149:    for row_index, row_values in enumerate(_paper_rows(solution), start=2):
      1151:            cell = worksheet.cell(row=row_index, column=column_index, value=value)
      1157:    summary_row = 2 + len(_paper_rows(solution)) + 1
      1158:    worksheet.cell(row=summary_row, column=1, value="最终烘干时长/h")
      1159:    duration_cell = worksheet.cell(
      1178:def validate_written_outputs(
      1181:    paper_path: str | Path = DEFAULT_PAPER_PATH,
      1182:    csv_path: str | Path = DEFAULT_CSV_PATH,
      1203:        worksheet.iter_rows(
      1273:    with Path(csv_path).open("r", newline="", encoding="utf-8") as stream:
      1274:        reader = csv.DictReader(stream)
      1277:        csv_rows = list(reader)
      1279:    expected_csv_rows = int(
      1284:    if len(csv_rows) != expected_csv_rows:
      1285:        raise ValueError(f"CSV行数为 {len(csv_rows)}，期望 {expected_csv_rows}")
      1287:        record_type: sum(row["record_type"] == record_type for row in csv_rows)
      1303:    csv_seen: set[tuple[str, str, str]] = set()
      1304:    max_csv_xlsx_difference = 0.0
      1305:    for row in csv_rows:
      1392:        if key in csv_seen:
      1394:        csv_seen.add(key)
      1400:        max_csv_xlsx_difference = max(
      1401:            max_csv_xlsx_difference, abs(actual_moisture - expected_moisture)
      1403:    if max_csv_xlsx_difference > 0.0:
      1406:    paper_workbook = load_workbook(Path(paper_path), read_only=True, data_only=True)
      1407:    if paper_workbook.sheetnames != ["表6"]:
      1408:        raise ValueError(f"论文表工作表错误: {paper_workbook.sheetnames}")
      1409:    paper_sheet = paper_workbook["表6"]
      1410:    paper_rows = list(
      1411:        paper_sheet.iter_rows(
      1413:            max_row=paper_sheet.max_row,
      1415:            max_col=paper_sheet.max_column,
      1419:    paper_hours = _paper_regular_hours(solution)
      1421:    expected_paper_rows = len(paper_hours) + 4
      1422:    if paper_sheet.max_row != expected_paper_rows or paper_sheet.max_column != 5:
      1424:            f"论文表尺寸错误: {(paper_sheet.max_row, paper_sheet.max_column)}，"
      1425:            f"期望 {(expected_paper_rows, 5)}"
      1427:    if list(paper_rows[0]) != ["时间/h", "0 cm", "0.5 cm", "1.0 cm", "药材表面"]:
      1429:    max_paper_difference = 0.0
      1430:    for row_index, hour in enumerate(paper_hours, start=1):
      1431:        row = paper_rows[row_index]
      1448:            max_paper_difference = max(
      1449:                max_paper_difference,
      1452:    termination_row_index = 1 + len(paper_hours) + 0
      1453:    termination_row = paper_rows[termination_row_index]
      1469:        max_paper_difference = max(
      1470:            max_paper_difference,
      1473:    summary_row = paper_rows[-1]
      1478:    if max_paper_difference > 0.0:
      1485:        "csv_rows": int(len(csv_rows)),
      1486:        "paper_rows": int(paper_sheet.max_row),
      1487:        "paper_columns": int(paper_sheet.max_column),
      1493:        "max_abs_csv_xlsx_difference": float(max_csv_xlsx_difference),
      1494:        "max_abs_paper_difference": float(max_paper_difference),
      1495:        "csv_record_counts": record_counts,
      1582:        write_result_xlsx(solution)
      1583:        write_result_csv(solution)
      1584:        write_paper_table(solution)
      1585:        output_summary = validate_written_outputs(solution)

## Activity

    Completed `/root/task4_solver`

## Activity

    agent tool: Wait · Completed

## Assistant

结果文件已生成，但尚未完成根模型终验。当前候选结论是 `52.370... h`? Wait typo maybe no. Need precise.

## Assistant

结果文件已生成，但尚未完成根模型终验。当前候选结论为 `52.3708637 h`；接下来只做两件事：审查输出实现是否严格符合模板/CSV 合同，以及让独立 `luna-worker` 从已提交版本重新运行全套验证。只有两者都通过才会作为最终结果汇报。

## Activity

    $ /bin/zsh -lc "git show --stat --oneline c4bc983 && git show --stat --oneline 2b0d204 && git status --short --branch && git diff --check && sed -n '840,1510p' solution/task4/script/solve_task4.py && printf '\\n--- CLI ---\\n' && sed -n '1510, emissions' solution/task4/script/solve_task4.py 2>/dev/null || true && sed -n '1510,1660p' solution/task4/script/solve_task4.py && printf '\\n--- CSV head/tail ---\\n' && sed -n '1,8p' solution/task4/answer.md 2>/dev/null || true && sed -n '1,8p' solution/task4/answer/task4_all_answers.csv && tail -8 solution/task4/answer/task4_all_answers.csv && printf '\\n--- answer sizes ---\\n' && ls -lh solution/task4/answer/*"
    status: Completed · exit 0
      c4bc983 实现问题四结果文件生成与验收
       solution/task4/script/solve_task4.py | 707 ++++++++++++++++++++++++++++++++++-
       1 file changed, 694 insertions(+), 13 deletions(-)
      2b0d204 生成问题四最终数值结果
       solution/task4/answer/result4.xlsx           |   Bin 0 -> 313581 bytes
       solution/task4/answer/task4_all_answers.csv  | 45366 +++++++++++++++++++++++++
       solution/task4/answer/task4_paper_table.xlsx |   Bin 0 -> 5360 bytes
       3 files changed, 45366 insertions(+)
      ## main...origin/main [ahead 4]
      ?? .DS_Store
      ?? solution/.DS_Store
      ?? solution/task2/.DS_Store
      ?? solution/task2/script/__pycache__/
              "kelvin_reference_D_m2_s": float(computed_D[0]),
          }
      
      
      def _regular_sample_indices(solution: dict[str, Any]) -> np.ndarray:
          """返回 result4/CSV 使用的 60 s 状态索引（严格从60 s开始）。"""
      
          times = np.asarray(solution["sampled_times_s"], dtype=float)
          termination_time = float(solution["termination_time_s"])
          last_time = np.floor(termination_time / OUTPUT_DT_S + 1.0e-12) * OUTPUT_DT_S
          indices = np.flatnonzero(
              (times >= OUTPUT_DT_S - 1.0e-8) & (times <= last_time + 1.0e-8)
          )
          selected = times[indices]
          if selected.size and not np.allclose(
              selected, np.arange(OUTPUT_DT_S, last_time + 0.1, OUTPUT_DT_S), atol=1.0e-8
          ):
              raise ValueError("求解器60 s状态与结果文件采样网格不一致")
          return indices
      
      
      def _paper_regular_hours(solution: dict[str, Any]) -> list[int]:
          """返回表6中的6 h、12 h、...常规行。"""
      
          termination_hours = float(solution["termination_time_s"]) / 3600.0
          last_regular_hour = int(np.floor(termination_hours / 6.0 + 1.0e-12) * 6)
          return list(range(6, last_regular_hour + 1, 6))
      
      
      def _sample_index_at_time(solution: dict[str, Any], time_s: float) -> int:
          times = np.asarray(solution["sampled_times_s"], dtype=float)
          matches = np.flatnonzero(np.isclose(times, time_s, rtol=0.0, atol=1.0e-8))
          if matches.size != 1:
              raise ValueError(f"缺少精确的 {time_s:g}s 完整xi状态")
          return int(matches[0])
      
      
      def _fixed_state_values(
          xi: np.ndarray,
          temperature_C: np.ndarray,
          moisture_kgkg: np.ndarray,
          radius_m: float,
      ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
          """按绝对半径采样；返回温度、水分和有效位置掩码。"""
      
          fixed_temperature = np.full(OUTPUT_RADIUS_CM.size, np.nan, dtype=float)
          fixed_moisture = np.full(OUTPUT_RADIUS_CM.size, np.nan, dtype=float)
          valid = OUTPUT_RADIUS_CM / 100.0 <= radius_m + 1.0e-12
          for index, radius_cm in enumerate(OUTPUT_RADIUS_CM):
              if not valid[index]:
                  continue
              xi_target = min(1.0, (radius_cm / 100.0) / radius_m)
              fixed_temperature[index] = float(np.interp(xi_target, xi, temperature_C))
              fixed_moisture[index] = float(np.interp(xi_target, xi, moisture_kgkg))
          return fixed_temperature, fixed_moisture, valid
      
      
      def _surface_values(
          temperature_C: np.ndarray, moisture_kgkg: np.ndarray
      ) -> tuple[float, float]:
          """药材表面直接取固定xi网格的 xi=1 节点。"""
      
          return float(temperature_C[-1]), float(moisture_kgkg[-1])
      
      
      def write_result_xlsx(
          solution: dict[str, Any],
          output_path: str | Path = DEFAULT_XLSX_PATH,
          template_path: str | Path = DEFAULT_TEMPLATE_PATH,
      ) -> None:
          """复制 result4 模板并写入60 s固定绝对位置和真实移动表面。"""
      
          output_path = Path(output_path)
          output_path.parent.mkdir(parents=True, exist_ok=True)
          workbook = load_workbook(Path(template_path))
          if workbook.sheetnames != ["Sheet1"]:
              raise ValueError(f"result4模板工作表不符合要求: {workbook.sheetnames}")
          worksheet = workbook["Sheet1"]
          header_style = copy(worksheet.cell(row=1, column=2)._style)
          time_style = copy(worksheet.cell(row=2, column=1)._style)
          value_style = copy(worksheet.cell(row=2, column=2)._style)
          if worksheet.max_row > 1:
              worksheet.delete_rows(2, worksheet.max_row - 1)
      
          # A1 保留官方模板语义；B:V 是固定绝对位置，W 是真实移动表面。
          worksheet.cell(row=1, column=1).value = "时间\\到药材中心的距离"
          for column_index, radius_cm in enumerate(OUTPUT_RADIUS_CM, start=2):
              cell = worksheet.cell(row=1, column=column_index, value=float(radius_cm))
              cell._style = copy(header_style)
              cell.number_format = "0.0"
          surface_header = worksheet.cell(row=1, column=OUTPUT_RADIUS_CM.size + 2, value="药材表面")
          surface_header._style = copy(header_style)
      
          xi = np.asarray(solution["xi"], dtype=float)
          sampled_indices = _regular_sample_indices(solution)
          sampled_times = np.asarray(solution["sampled_times_s"], dtype=float)
          sampled_radius = np.asarray(solution["sampled_radius_m"], dtype=float)
          sampled_temperature = np.asarray(
              solution["sampled_temperature_internal_C"], dtype=float
          )
          sampled_moisture = np.asarray(
              solution["sampled_moisture_internal_kgkg"], dtype=float
          )
          for row_index, state_index in enumerate(sampled_indices, start=2):
              time_cell = worksheet.cell(row=row_index, column=1, value=int(round(sampled_times[state_index])))
              time_cell._style = copy(time_style)
              time_cell.number_format = "0"
              _, fixed_moisture, valid = _fixed_state_values(
                  xi,
                  sampled_temperature[state_index],
                  sampled_moisture[state_index],
                  float(sampled_radius[state_index]),
              )
              for column_index, (value, is_valid) in enumerate(
                  zip(fixed_moisture, valid), start=2
              ):
                  cell = worksheet.cell(row=row_index, column=column_index)
                  cell._style = copy(value_style)
                  if is_valid:
                      cell.value = float(f"{value:.4f}")
                      cell.number_format = "0.0000"
                  else:
                      cell.value = None
              surface_value = float(f"{sampled_moisture[state_index, -1]:.4f}")
              surface_cell = worksheet.cell(
                  row=row_index, column=OUTPUT_RADIUS_CM.size + 2, value=surface_value
              )
              surface_cell._style = copy(value_style)
              surface_cell.number_format = "0.0000"
          workbook.save(output_path)
      
      
      def _csv_state_rows(
          record_prefix: str,
          time_s: float,
          radius_m: float,
          temperature_C: np.ndarray,
          moisture_kgkg: np.ndarray,
          xi: np.ndarray,
          sample_time: bool,
      ) -> list[dict[str, str]]:
          """将一个完整xi状态展开为固定位置记录和单独表面记录。"""
      
          fixed_temperature, fixed_moisture, valid = _fixed_state_values(
              xi, temperature_C, moisture_kgkg, radius_m
          )
          if sample_time:
              time_token = str(int(round(time_s)))
              fixed_type = "sample_fixed"
              surface_type = "sample_surface"
          else:
              time_token = f"{time_s:.6f}"
              fixed_type = "drying_end_fixed"
              surface_type = "drying_end_surface"
          hour_token = f"{time_s / 3600.0:.8f}"
          radius_token = f"{radius_m * 100.0:.4f}"
          rows: list[dict[str, str]] = []
          for index, radius_cm in enumerate(OUTPUT_RADIUS_CM):
              if not valid[index]:
                  continue
              rows.append(
                  {
                      "record_type": fixed_type,
                      "time_s": time_token,
                      "time_h": hour_token,
                      "radius_cm": radius_token,
                      "r_cm": f"{radius_cm:.4f}",
                      "is_surface": "0",
                      "temperature_C": f"{fixed_temperature[index]:.4f}",
                      "moisture_kgkg": f"{fixed_moisture[index]:.4f}",
                  }
              )
          surface_temperature, surface_moisture = _surface_values(
              temperature_C, moisture_kgkg
          )
          rows.append(
              {
                  "record_type": surface_type,
                  "time_s": time_token,
                  "time_h": hour_token,
                  "radius_cm": radius_token,
                  "r_cm": radius_token,
                  "is_surface": "1",
                  "temperature_C": f"{surface_temperature:.4f}",
                  "moisture_kgkg": f"{surface_moisture:.4f}",
              }
          )
          return rows
      
      
      def write_result_csv(
          solution: dict[str, Any], output_path: str | Path = DEFAULT_CSV_PATH
      ) -> None:
          """写入包含固定位置、真实表面和终止状态的完整长表CSV。"""
      
          output_path = Path(output_path)
          output_path.parent.mkdir(parents=True, exist_ok=True)
          xi = np.asarray(solution["xi"], dtype=float)
          sampled_indices = _regular_sample_indices(solution)
          sampled_times = np.asarray(solution["sampled_times_s"], dtype=float)
          sampled_radius = np.asarray(solution["sampled_radius_m"], dtype=float)
          sampled_temperature = np.asarray(
              solution["sampled_temperature_internal_C"], dtype=float
          )
          sampled_moisture = np.asarray(
              solution["sampled_moisture_internal_kgkg"], dtype=float
          )
          rows: list[dict[str, str]] = []
          for state_index in sampled_indices:
              rows.extend(
                  _csv_state_rows(
                      "sample",
                      float(sampled_times[state_index]),
                      float(sampled_radius[state_index]),
                      sampled_temperature[state_index],
                      sampled_moisture[state_index],
                      xi,
                      sample_time=True,
                  )
              )
          rows.extend(
              _csv_state_rows(
                  "drying_end",
                  float(solution["termination_time_s"]),
                  float(solution["termination_radius_m"]),
                  np.asarray(solution["termination_temperature_internal_C"], dtype=float),
                  np.asarray(solution["termination_moisture_internal_kgkg"], dtype=float),
                  xi,
                  sample_time=False,
              )
          )
          with output_path.open("w", newline="", encoding="utf-8") as stream:
              writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
              writer.writeheader()
              writer.writerows(rows)
      
      
      def _paper_rows(solution: dict[str, Any]) -> list[list[Any]]:
          """生成表6的常规6 h行和精确终止行。"""
      
          xi = np.asarray(solution["xi"], dtype=float)
          sampled_radius = np.asarray(solution["sampled_radius_m"], dtype=float)
          sampled_temperature = np.asarray(
              solution["sampled_temperature_internal_C"], dtype=float
          )
          sampled_moisture = np.asarray(
              solution["sampled_moisture_internal_kgkg"], dtype=float
          )
          rows: list[list[Any]] = []
          for hour in _paper_regular_hours(solution):
              state_index = _sample_index_at_time(solution, hour * 3600.0)
              _, fixed_moisture, valid = _fixed_state_values(
                  xi,
                  sampled_temperature[state_index],
                  sampled_moisture[state_index],
                  float(sampled_radius[state_index]),
              )
              _, surface_moisture = _surface_values(
                  sampled_temperature[state_index], sampled_moisture[state_index]
              )
              rows.append(
                  [
                      float(hour),
                      float(fixed_moisture[0]) if valid[0] else None,
                      float(fixed_moisture[5]) if valid[5] else None,
                      float(fixed_moisture[10]) if valid[10] else None,
                      float(surface_moisture),
                  ]
              )
          termination_moisture = np.asarray(
              solution["termination_moisture_internal_kgkg"], dtype=float
          )
          termination_temperature = np.asarray(
              solution["termination_temperature_internal_C"], dtype=float
          )
          _, fixed_moisture, valid = _fixed_state_values(
              xi,
              termination_temperature,
              termination_moisture,
              float(solution["termination_radius_m"]),
          )
          _, surface_moisture = _surface_values(termination_temperature, termination_moisture)
          termination_hours = float(solution["termination_time_s"]) / 3600.0
          rows.append(
              [
                  f"烘干结束时间（{termination_hours:.4f} h）",
                  float(fixed_moisture[0]) if valid[0] else None,
                  float(fixed_moisture[5]) if valid[5] else None,
                  float(fixed_moisture[10]) if valid[10] else None,
                  float(surface_moisture),
              ]
          )
          return rows
      
      
      def write_paper_table(
          solution: dict[str, Any], output_path: str | Path = DEFAULT_PAPER_PATH
      ) -> None:
          """生成论文表6工作表，不把绝对位置之外的数值外推到表格中。"""
      
          output_path = Path(output_path)
          output_path.parent.mkdir(parents=True, exist_ok=True)
          workbook = Workbook()
          worksheet = workbook.active
          worksheet.title = "表6"
          headers = ["时间/h", "0 cm", "0.5 cm", "1.0 cm", "药材表面"]
          for column_index, header in enumerate(headers, start=1):
              cell = worksheet.cell(row=1, column=column_index, value=header)
              cell.font = Font(bold=True)
          for row_index, row_values in enumerate(_paper_rows(solution), start=2):
              for column_index, value in enumerate(row_values, start=1):
                  cell = worksheet.cell(row=row_index, column=column_index, value=value)
                  if column_index == 1 and isinstance(value, (int, float)):
                      cell.number_format = "0.0"
                  elif column_index > 1 and value is not None:
                      cell.value = float(f"{float(value):.4f}")
                      cell.number_format = "0.0000"
          summary_row = 2 + len(_paper_rows(solution)) + 1
          worksheet.cell(row=summary_row, column=1, value="最终烘干时长/h")
          duration_cell = worksheet.cell(
              row=summary_row,
              column=2,
              value=float(f"{float(solution['termination_time_s']) / 3600.0:.4f}"),
          )
          duration_cell.number_format = "0.0000"
          workbook.save(output_path)
      
      
      def _fixed_valid_count(
          radius_m: float,
      ) -> int:
          return int(np.count_nonzero(OUTPUT_RADIUS_CM / 100.0 <= radius_m + 1.0e-12))
      
      
      def _format_pattern_ok(value: str, decimals: int) -> bool:
          return re.fullmatch(rf"\d+\.\d{{{decimals}}}", value) is not None
      
      
      def validate_written_outputs(
          solution: dict[str, Any],
          xlsx_path: str | Path = DEFAULT_XLSX_PATH,
          paper_path: str | Path = DEFAULT_PAPER_PATH,
          csv_path: str | Path = DEFAULT_CSV_PATH,
      ) -> dict[str, Any]:
          """独立回读三个文件并检查结构、掩码、格式及全量数值一致性。"""
      
          summary = validate_solution(solution)
          xi = np.asarray(solution["xi"], dtype=float)
          sampled_indices = _regular_sample_indices(solution)
          sampled_times = np.asarray(solution["sampled_times_s"], dtype=float)
          sampled_radius = np.asarray(solution["sampled_radius_m"], dtype=float)
          sampled_temperature = np.asarray(
              solution["sampled_temperature_internal_C"], dtype=float
          )
          sampled_moisture = np.asarray(
              solution["sampled_moisture_internal_kgkg"], dtype=float
          )
      
          workbook = load_workbook(Path(xlsx_path), read_only=True, data_only=True)
          if workbook.sheetnames != ["Sheet1"]:
              raise ValueError(f"result4答案工作表错误: {workbook.sheetnames}")
          worksheet = workbook["Sheet1"]
          xlsx_rows = list(
              worksheet.iter_rows(
                  min_row=1,
                  max_row=worksheet.max_row,
                  min_col=1,
                  max_col=worksheet.max_column,
                  values_only=True,
              )
          )
          expected_xlsx_rows = sampled_indices.size + 1
          expected_xlsx_columns = OUTPUT_RADIUS_CM.size + 2
          if worksheet.max_row != expected_xlsx_rows or worksheet.max_column != expected_xlsx_columns:
              raise ValueError(
                  f"result4尺寸错误: {(worksheet.max_row, worksheet.max_column)}，"
                  f"期望 {(expected_xlsx_rows, expected_xlsx_columns)}"
              )
          header = xlsx_rows[0]
          expected_header = ["时间\\到药材中心的距离"] + [
              float(radius) for radius in OUTPUT_RADIUS_CM
          ] + ["药材表面"]
          header_positions_ok = (
              len(header) == len(expected_header)
              and header[0] == expected_header[0]
              and header[-1] == expected_header[-1]
              and np.allclose(
                  np.asarray(header[1:-1], dtype=float), OUTPUT_RADIUS_CM, rtol=0.0, atol=1.0e-12
              )
          )
          if not header_positions_ok:
              raise ValueError(f"result4表头错误: {header!r}")
          fixed_blank_count = 0
          max_xlsx_expected_difference = 0.0
          xlsx_fixed_map: dict[tuple[int, str], float] = {}
          xlsx_surface_map: dict[int, float] = {}
          for row_offset, state_index in enumerate(sampled_indices, start=1):
              row = xlsx_rows[row_offset]
              expected_time = int(round(sampled_times[state_index]))
              if row[0] != expected_time:
                  raise ValueError("result4时间行不是严格60 s整数网格")
              fixed_temperature, expected_moisture, valid = _fixed_state_values(
                  xi,
                  sampled_temperature[state_index],
                  sampled_moisture[state_index],
                  float(sampled_radius[state_index]),
              )
              del fixed_temperature
              for position_index, is_valid in enumerate(valid):
                  value = row[position_index + 1]
                  if not is_valid:
                      fixed_blank_count += 1
                      if value is not None:
                          raise ValueError("result4在移动表面之外存在外推值")
                      continue
                  if value is None or not np.isfinite(float(value)) or float(value) < 0.0:
                      raise ValueError("result4固定位置包含空值、非有限值或负水分")
                  expected_value = float(f"{expected_moisture[position_index]:.4f}")
                  max_xlsx_expected_difference = max(
                      max_xlsx_expected_difference, abs(float(value) - expected_value)
                  )
                  xlsx_fixed_map[(expected_time, f"{OUTPUT_RADIUS_CM[position_index]:.4f}")] = float(value)
              surface_value = row[-1]
              if surface_value is None or not np.isfinite(float(surface_value)) or float(surface_value) < 0.0:
                  raise ValueError("result4表面列包含无效水分")
              expected_surface = float(f"{sampled_moisture[state_index, -1]:.4f}")
              max_xlsx_expected_difference = max(
                  max_xlsx_expected_difference, abs(float(surface_value) - expected_surface)
              )
              xlsx_surface_map[expected_time] = float(surface_value)
          if max_xlsx_expected_difference > 0.0:
              raise ValueError("result4回读值与求解器四位小数结果不一致")
      
          with Path(csv_path).open("r", newline="", encoding="utf-8") as stream:
              reader = csv.DictReader(stream)
              if reader.fieldnames != CSV_COLUMNS:
                  raise ValueError(f"CSV字段错误: {reader.fieldnames!r}")
              csv_rows = list(reader)
          termination_radius = float(solution["termination_radius_m"])
          expected_csv_rows = int(
              sum(_fixed_valid_count(float(sampled_radius[index])) + 1 for index in sampled_indices)
              + _fixed_valid_count(termination_radius)
              + 1
          )
          if len(csv_rows) != expected_csv_rows:
              raise ValueError(f"CSV行数为 {len(csv_rows)}，期望 {expected_csv_rows}")
          record_counts = {
              record_type: sum(row["record_type"] == record_type for row in csv_rows)
              for record_type in (
                  "sample_fixed",
                  "sample_surface",
                  "drying_end_fixed",
                  "drying_end_surface",
              )
          }
          expected_record_counts = {
              "sample_fixed": int(sum(_fixed_valid_count(float(sampled_radius[index])) for index in sampled_indices)),
              "sample_surface": int(sampled_indices.size),
              "drying_end_fixed": _fixed_valid_count(termination_radius),
              "drying_end_surface": 1,
          }
          if record_counts != expected_record_counts:
              raise ValueError(f"CSV record_type结构错误: {record_counts!r}")
          csv_seen: set[tuple[str, str, str]] = set()
          max_csv_xlsx_difference = 0.0
          for row in csv_rows:
              record_type = row["record_type"]
              if record_type not in expected_record_counts:
                  raise ValueError(f"CSV包含未知record_type: {record_type}")
              if not _format_pattern_ok(row["time_h"], 8):
                  raise ValueError("CSV time_h 不是八位小数")
              if not np.isclose(
                  float(row["time_h"]), float(row["time_s"]) / 3600.0, rtol=0.0, atol=5.0e-9
              ):
                  raise ValueError("CSV time_h 与 time_s 不一致")
              if not _format_pattern_ok(row["radius_cm"], 4) or not _format_pattern_ok(row["r_cm"], 4):
                  raise ValueError("CSV半径字段不是四位小数")
              if not _format_pattern_ok(row["temperature_C"], 4) or not _format_pattern_ok(row["moisture_kgkg"], 4):
                  raise ValueError("CSV温度/水分不是四位小数字符串")
              if row["is_surface"] not in {"0", "1"}:
                  raise ValueError("CSV is_surface 不是0/1")
              if record_type.startswith("sample_"):
                  if re.fullmatch(r"\d+", row["time_s"]) is None:
                      raise ValueError("CSV sample time_s 不是整数秒")
                  sample_time = int(row["time_s"])
                  if sample_time not in xlsx_surface_map and record_type == "sample_surface":
                      raise ValueError("CSV sample表面时刻无法对应result4")
                  sample_matches = np.flatnonzero(
                      np.isclose(sampled_times, sample_time, rtol=0.0, atol=1.0e-8)
                  )
                  if sample_matches.size != 1:
                      raise ValueError("CSV sample时刻无法对应求解器状态")
                  expected_sample_radius_cm = float(sampled_radius[sample_matches[0]]) * 100.0
                  if not np.isclose(
                      float(row["radius_cm"]), expected_sample_radius_cm, rtol=0.0, atol=5.0e-5
                  ):
                      raise ValueError("CSV sample radius_cm 与 R(t) 不一致")
                  if record_type == "sample_fixed":
                      key = (sample_time, row["r_cm"])
                      if key not in xlsx_fixed_map:
                          raise ValueError("CSV fixed记录无法对应result4固定位置")
                      if row["is_surface"] != "0":
                          raise ValueError("CSV fixed记录的is_surface必须为0")
                      expected_moisture = xlsx_fixed_map[key]
                  else:
                      if not np.isclose(
                          float(row["r_cm"]), expected_sample_radius_cm, rtol=0.0, atol=5.0e-5
                      ):
                          raise ValueError("CSV sample表面 r_cm 与 R(t) 不一致")
                      expected_moisture = xlsx_surface_map[sample_time]
              else:
                  if re.fullmatch(r"\d+\.\d{6}", row["time_s"]) is None:
                      raise ValueError("CSV终止 time_s 不是六位小数")
                  termination_time = float(row["time_s"])
                  if not np.isclose(termination_time, float(solution["termination_time_s"]), atol=5.0e-7, rtol=0.0):
                      raise ValueError("CSV终止时刻与求解器不一致")
                  if not np.isclose(
                      float(row["radius_cm"]), termination_radius * 100.0, rtol=0.0, atol=5.0e-5
                  ):
                      raise ValueError("CSV终止 radius_cm 与真实表面半径不一致")
                  termination_temperature = np.asarray(solution["termination_temperature_internal_C"], dtype=float)
                  termination_moisture_array = np.asarray(solution["termination_moisture_internal_kgkg"], dtype=float)
                  fixed_temperature, fixed_moisture, valid = _fixed_state_values(
                      xi, termination_temperature, termination_moisture_array, termination_radius
                  )
                  del fixed_temperature
                  if record_type == "drying_end_fixed":
                      radius_index = int(round(float(row["r_cm"]) * 10.0))
                      if (
                          radius_index < 0
                          or radius_index >= OUTPUT_RADIUS_CM.size
                          or not valid[radius_index]
                          or not np.isclose(
                              float(row["r_cm"]),
                              float(OUTPUT_RADIUS_CM[radius_index]),
                              rtol=0.0,
                              atol=5.0e-5,
                          )
                      ):
                          raise ValueError("CSV终止固定位置无效")
                      if row["is_surface"] != "0":
                          raise ValueError("CSV终止fixed记录的is_surface必须为0")
                      expected_moisture = float(f"{fixed_moisture[radius_index]:.4f}")
                  else:
                      if not np.isclose(
                          float(row["radius_cm"]), termination_radius * 100.0, rtol=0.0, atol=5.0e-5
                      ) or not np.isclose(
                          float(row["r_cm"]), termination_radius * 100.0, rtol=0.0, atol=5.0e-5
                      ):
                          raise ValueError("CSV终止表面半径字段错误")
                      expected_moisture = float(f"{termination_moisture_array[-1]:.4f}")
              key = (record_type, row["time_s"], row["r_cm"])
              if key in csv_seen:
                  raise ValueError("CSV存在重复记录")
              csv_seen.add(key)
              if (record_type.endswith("surface")) != (row["is_surface"] == "1"):
                  raise ValueError("CSV surface标记与record_type不一致")
              actual_moisture = float(row["moisture_kgkg"])
              if not np.isfinite(actual_moisture) or actual_moisture < 0.0:
                  raise ValueError("CSV水分包含非有限值或负值")
              max_csv_xlsx_difference = max(
                  max_csv_xlsx_difference, abs(actual_moisture - expected_moisture)
              )
          if max_csv_xlsx_difference > 0.0:
              raise ValueError("CSV与result4对应水分值不一致")
      
          paper_workbook = load_workbook(Path(paper_path), read_only=True, data_only=True)
          if paper_workbook.sheetnames != ["表6"]:
              raise ValueError(f"论文表工作表错误: {paper_workbook.sheetnames}")
          paper_sheet = paper_workbook["表6"]
          paper_rows = list(
              paper_sheet.iter_rows(
                  min_row=1,
                  max_row=paper_sheet.max_row,
                  min_col=1,
                  max_col=paper_sheet.max_column,
                  values_only=True,
              )
          )
          paper_hours = _paper_regular_hours(solution)
          # 表头 + 常规行 + 终止行 + 一个空行 + 最终时长摘要行。
          expected_paper_rows = len(paper_hours) + 4
          if paper_sheet.max_row != expected_paper_rows or paper_sheet.max_column != 5:
              raise ValueError(
                  f"论文表尺寸错误: {(paper_sheet.max_row, paper_sheet.max_column)}，"
                  f"期望 {(expected_paper_rows, 5)}"
              )
          if list(paper_rows[0]) != ["时间/h", "0 cm", "0.5 cm", "1.0 cm", "药材表面"]:
              raise ValueError("论文表表头错误")
          max_paper_difference = 0.0
          for row_index, hour in enumerate(paper_hours, start=1):
              row = paper_rows[row_index]
              if not np.isclose(float(row[0]), hour, atol=1.0e-12, rtol=0.0):
                  raise ValueError("论文表常规时间行错误")
              expected_index = _sample_index_at_time(solution, hour * 3600.0)
              _, fixed_moisture, valid = _fixed_state_values(
                  xi,
                  sampled_temperature[expected_index],
                  sampled_moisture[expected_index],
                  float(sampled_radius[expected_index]),
              )
              expected_values = [fixed_moisture[0], fixed_moisture[5], fixed_moisture[10], sampled_moisture[expected_index, -1]]
              for column_index, expected_value in enumerate(expected_values, start=1):
                  if expected_value is None or (column_index <= 3 and not valid[[0, 5, 10][column_index - 1]]):
                      continue
                  actual_value = row[column_index]
                  if actual_value is None or not np.isfinite(float(actual_value)):
                      raise ValueError("论文表常规水分为空或非有限")
                  max_paper_difference = max(
                      max_paper_difference,
                      abs(float(actual_value) - float(f"{expected_value:.4f}")),
                  )
          termination_row_index = 1 + len(paper_hours) + 0
          termination_row = paper_rows[termination_row_index]
          expected_termination_text = f"烘干结束时间（{float(solution['termination_time_s']) / 3600.0:.4f} h）"
          if termination_row[0] != expected_termination_text:
              raise ValueError("论文表终止时间文本错误")
          termination_temperature = np.asarray(solution["termination_temperature_internal_C"], dtype=float)
          termination_moisture_array = np.asarray(solution["termination_moisture_internal_kgkg"], dtype=float)
          _, fixed_moisture, valid = _fixed_state_values(
              xi, termination_temperature, termination_moisture_array, termination_radius
          )
          expected_values = [fixed_moisture[0], fixed_moisture[5], fixed_moisture[10], termination_moisture_array[-1]]
          for column_index, expected_value in enumerate(expected_values, start=1):
              if column_index <= 3 and not valid[[0, 5, 10][column_index - 1]]:
                  continue
              actual_value = termination_row[column_index]
              if actual_value is None or not np.isfinite(float(actual_value)):
                  raise ValueError("论文表终止水分为空或非有限")
              max_paper_difference = max(
                  max_paper_difference,
                  abs(float(actual_value) - float(f"{expected_value:.4f}")),
              )
          summary_row = paper_rows[-1]
          if summary_row[0] != "最终烘干时长/h" or not np.isclose(
              float(summary_row[1]), float(solution["termination_time_s"]) / 3600.0, atol=5.0e-5
          ):
              raise ValueError("论文表最终烘干时长摘要错误")
          if max_paper_difference > 0.0:
              raise ValueError("论文表水分值与求解器结果不一致")
      
          return {
              **summary,
              "xlsx_rows": int(worksheet.max_row),
              "xlsx_columns": int(worksheet.max_column),
              "csv_rows": int(len(csv_rows)),
              "paper_rows": int(paper_sheet.max_row),
              "paper_columns": int(paper_sheet.max_column),
              "sample_start_s": int(round(sampled_times[sampled_indices[0]])) if sampled_indices.size else None,
              "sample_end_s": int(round(sampled_times[sampled_indices[-1]])) if sampled_indices.size else None,
              "sample_count": int(sampled_indices.size),
              "fixed_blank_count": int(fixed_blank_count),
              "max_abs_xlsx_expected_difference": float(max_xlsx_expected_difference),
              "max_abs_csv_xlsx_difference": float(max_csv_xlsx_difference),
              "max_abs_paper_difference": float(max_paper_difference),
              "csv_record_counts": record_counts,
          }
      
      
      def run_coarse_comparison(
          air_data_path: str | Path = DEFAULT_AIR_DATA_PATH,
          radius_data_path: str | Path = DEFAULT_RADIUS_DATA_PATH,
          max_time_s: float = DEFAULT_MAX_TIME_S,
          progress: bool = False,
      ) -> dict[str, Any]:
          """运行 N=160、dt=1 s 的粗网格对照解。"""
      
          solution = solve_task4(
              air_data_path=air_data_path,
              radius_data_path=radius_data_path,
              max_time_s=max_time_s,
      
      --- CLI ---
              max_time_s=max_time_s,
              time_step_s=1.0,
              output_dt_s=OUTPUT_DT_S,
              n_intervals=160,
              progress=progress,
          )
          return validate_solution(solution)
      
      
      def main() -> None:
          parser = argparse.ArgumentParser(description="求解A题问题四移动边界模型")
          parser.add_argument("--air-data-path", type=Path, default=DEFAULT_AIR_DATA_PATH)
          parser.add_argument("--radius-data-path", type=Path, default=DEFAULT_RADIUS_DATA_PATH)
          parser.add_argument("--max-time", type=float, default=DEFAULT_MAX_TIME_S)
          parser.add_argument("--time-step", type=float, default=TIME_STEP_S_DEFAULT)
          parser.add_argument("--output-dt", type=float, default=OUTPUT_DT_S)
          parser.add_argument("--n", type=int, default=N_DEFAULT)
          parser.add_argument("--no-write", action="store_true", help="本阶段不生成答案文件")
          parser.add_argument(
              "--skip-sensitivity",
              action="store_true",
              help="跳过 N=160、dt=1 s 的粗网格对照计算",
          )
          parser.add_argument("--progress", action="store_true", help="按6 h打印推进进度")
          args = parser.parse_args()
      
          started = wall_time.perf_counter()
          print(
              "问题四最终加密解开始: "
              f"N={args.n}, dxi={1.0 / args.n:g}, dt={args.time_step:g}s, "
              f"output_dt={args.output_dt:g}s, threshold C<{DRYING_THRESHOLD_KGKG:g}"
          )
          solution = solve_task4(
              air_data_path=args.air_data_path,
              radius_data_path=args.radius_data_path,
              max_time_s=args.max_time,
              time_step_s=args.time_step,
              output_dt_s=args.output_dt,
              n_intervals=args.n,
              progress=args.progress,
          )
          summary = validate_solution(solution)
          print(f"最终加密解数值检查: {summary}")
          print(
              "终止证据: "
              f"lower t={summary['termination_lower_time_s']:.6f}s "
              f"max C={summary['termination_lower_max_kgkg']:.8f}; "
              f"upper t={summary['termination_time_s']:.6f}s "
              f"max C={summary['termination_max_kgkg']:.8f}; "
              f"R={summary['termination_radius_cm']:.6f}cm, "
              f"max位置 r={summary['termination_max_radius_cm']:.6f}cm "
              f"(xi={summary['termination_max_xi']:.6f})"
          )
          if not args.skip_sensitivity:
              coarse_started = wall_time.perf_counter()
              coarse_summary = run_coarse_comparison(
                  air_data_path=args.air_data_path,
                  radius_data_path=args.radius_data_path,
                  max_time_s=args.max_time,
                  progress=args.progress,
              )
              print(f"N=160, dt=1s 粗网格对照: {coarse_summary}")
              print(
                  f"结束时间差（加密-粗解）: "
                  f"{summary['termination_time_h'] - coarse_summary['termination_time_h']:.8f} h"
              )
              print(
                  f"粗网格对照耗时: {wall_time.perf_counter() - coarse_started:.2f}s"
              )
          if args.no_write:
              print("--no-write: 本阶段未生成任何 answer 文件")
          else:
              write_result_xlsx(solution)
              write_result_csv(solution)
              write_paper_table(solution)
              output_summary = validate_written_outputs(solution)
              print(f"答案文件回读验收: {output_summary}")
              print(f"已生成: {DEFAULT_XLSX_PATH}")
              print(f"已生成: {DEFAULT_PAPER_PATH}")
              print(f"已生成: {DEFAULT_CSV_PATH}")
          print(f"总耗时: {wall_time.perf_counter() - started:.2f}s")
      
      
      if __name__ == "__main__":
          main()
      
      --- CSV head/tail ---
      record_type,time_s,time_h,radius_cm,r_cm,is_surface,temperature_C,moisture_kgkg
      sample_fixed,60,0.01666667,1.9958,0.0000,0,28.0000,2.5500
      sample_fixed,60,0.01666667,1.9958,0.1000,0,28.0000,2.5500
      sample_fixed,60,0.01666667,1.9958,0.2000,0,28.0000,2.5500
      sample_fixed,60,0.01666667,1.9958,0.3000,0,28.0000,2.5500
      sample_fixed,60,0.01666667,1.9958,0.4000,0,28.0000,2.5500
      sample_fixed,60,0.01666667,1.9958,0.5000,0,28.0000,2.5500
      sample_fixed,60,0.01666667,1.9958,0.6000,0,28.0000,2.5500
      drying_end_fixed,188535.109375,52.37086372,1.2000,0.6000,0,50.1650,0.1372
      drying_end_fixed,188535.109375,52.37086372,1.2000,0.7000,0,50.1650,0.1321
      drying_end_fixed,188535.109375,52.37086372,1.2000,0.8000,0,50.1650,0.1259
      drying_end_fixed,188535.109375,52.37086372,1.2000,0.9000,0,50.1650,0.1181
      drying_end_fixed,188535.109375,52.37086372,1.2000,1.0000,0,50.1650,0.1081
      drying_end_fixed,188535.109375,52.37086372,1.2000,1.1000,0,50.1650,0.0936
      drying_end_fixed,188535.109375,52.37086372,1.2000,1.2000,0,50.1650,0.0525
      drying_end_surface,188535.109375,52.37086372,1.2000,1.2000,1,50.1650,0.0525
      
      --- answer sizes ---
      -rw-r--r--@ 1 jiaqiaosu  staff   306K Sep 11 00:55 solution/task4/answer/result4.xlsx
      -rw-r--r--@ 1 jiaqiaosu  staff   2.7M Sep 11 00:55 solution/task4/answer/task4_all_answers.csv
      -rw-r--r--@ 1 jiaqiaosu  staff   5.2K Sep 11 00:55 solution/task4/answer/task4_paper_table.xlsx

## Activity

    Started `/root/task4_final_audit`

## Activity

    agent tool: Wait · Completed

## Assistant

独立终验正在重跑最终解和粗解，预计主要耗时约 2–3 分钟。代码审查目前未发现新的模型偏差；特别确认脚本使用的是归一化控制体测度，因此表面项写成 `h/R`、`h_m/R` 与写成物理控制体测度时的 `R·h`、`R·h_m` 完全等价，量纲正确。

## Activity

    Completed `/root/task4_final_audit`

## Activity

    agent tool: Wait · Completed

## Assistant

独立终验已通过，复现了全部数值和三文件逐点一致性。唯一遗留是审计导入 Python 模块时生成了 `solution/task4/script/__pycache__/...pyc`；这是未跟踪副产物，不属于答案。我将让产生它的 worker 精确清理该目录，并再次确认 task4 无未提交内容；不会处理仓库原有的其他 `.DS_Store` 或 task2 缓存。

## Activity

    Interacted with `/root/task4_final_audit`

## Activity

    Completed `/root/task4_final_audit`

## Activity

    agent tool: Wait · Completed

## Assistant

问题四已完成真实数值求解并通过独立复算验收。

- 最终烘干时长：`52.3708637 h`（`188535.109375 s`）
- 结束时 \(C_{\max}\)：`0.149999999779 kg/kg`
- 最大值位置：药材中心，`ξ=0，r=0 cm`
- 此时实际半径：`1.2000 cm`
- 结束前时刻：`188535.108398 s`
- 结束前 \(C_{\max}\)：`0.150000000284 kg/kg`

移动边界采用固定域变换 \(\xi=r/R(t)\)，显式保留 \(-(\dot R/R)\xi\,\partial/\partial\xi\) 移动坐标项；附件2半径采用分段线性插值，表面边界始终作用于真实的 \(r=R(t)\)。

相比问题三，核心修改为：

1. 固定半径改为附件2给出的 \(R(t)\)；
2. 采用附录4的 \(\rho,c_p,k,D\) 公式，且 \(D\) 中温度使用 Kelvin；
3. 在固定 \(\xi\) 网格中加入移动坐标项和随半径变化的扩散、表面边界系数；
4. 环境条件、初始条件及对流换热/传质系数保持不变。

问题三烘干时间为 `57.0875 h`，问题四提前 `4.7166 h`，约 `8.2621%`；差异由附录4物性、半径收缩及移动边界共同造成。

数值敏感性：

- 最终解：`N=320，dt=0.5 s` → `52.3708637 h`
- 粗解：`N=160，dt=1 s` → `52.3510623 h`
- 差值：`0.0198014 h`（约 `71.29 s`，相对差 `0.0378%`）

最终文件：

- [result4.xlsx](/Users/jiaqiaosu/Desktop/作业/2026夏季学期/2026CUMCM/2026CUMCM/solution/task4/answer/result4.xlsx)
- [task4_paper_table.xlsx](/Users/jiaqiaosu/Desktop/作业/2026夏季学期/2026CUMCM/2026CUMCM/solution/task4/answer/task4_paper_table.xlsx)
- [task4_all_answers.csv](/Users/jiaqiaosu/Desktop/作业/2026夏季学期/2026CUMCM/2026CUMCM/solution/task4/answer/task4_all_answers.csv)

三文件回读一致性最大差为 `0`；`result4.xlsx` 的越界固定坐标均为空，动态表面列使用真实表面值。

最终 Git commit：

`2b0d204d040e49e39e39ab4e4efbc39cdedb6573`

剩余问题：无。`solution/task4` 无未提交修改；仓库原有的非 task4 `.DS_Store` 和 task2 缓存未触碰。
