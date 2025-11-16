
import asyncio
import json
from typing import TYPE_CHECKING, Dict, Any

# --- HARD CODED PROJECT SETTINGS ---
import vertexai
vertexai.init(
    project="cloud-run-hackathon-477510",
    project_number="85229041043",
    location="europe-west4"
)

from vertexai.generative_models import GenerativeModel

if TYPE_CHECKING:
    from session import Session

# ------------------------------------------------------------------
# Base Agent
# ------------------------------------------------------------------
class Agent:
    def __init__(self, node_id: str, config: Dict[str, Any], session: "Session"):
        self.node_id = node_id
        self.config = config
        self.session = session
        self.role = config.get("role", "Unnamed Agent")

    async def think(self, seconds: float = 1.0):
        await asyncio.sleep(seconds)

    def speak(self, text: str):
        print(f"[{self.role}]: {text}")
        self.session.add_message(self.role, text)

    async def generate_response(self, prompt: str) -> str:
        try:
            model_name = self.config.get("llm", "gemini-1.5-flash")
            system = f"You are a concise {self.role}."
            model = GenerativeModel(model_name, system_instruction=system)
            resp = await model.generate_content_async(prompt)
            return resp.text.strip()
        except Exception as e:
            return f"API error: {e}"

# ------------------------------------------------------------------
# CoderAgent – JSON-ONLY, BULLETPROOF
# ------------------------------------------------------------------
class CoderAgent(Agent):
        # --------------------------------------------------------------
    # CoderAgent – FINAL: TEMPLATE + FILL-IN-THE-BLANK ONLY
    # --------------------------------------------------------------
    async def run_finalization(self, vibe: str, instructions: str | None = None):
        self.speak(f"Deploying bulletproof game for: '{vibe}'.")
        await self.think(1)

        # Extract key nouns for procedural logic
        keywords = vibe.lower().split()
        is_cookie = any(w in keywords for w in ['cookie', 'biscuit', 'crumb'])
        is_penguin = any(w in keywords for w in ['penguin', 'slide', 'icy', 'hill'])
        is_goose = any(w in keywords for w in ['goose', 'honk', 'untitled'])
        is_book = any(w in keywords for w in ['book', 'page', 'story'])

        # BULLETPROOF BASE TEMPLATE (never breaks)
        base_html = f"""<!DOCTYPE html>
<html><head><title>{vibe}</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{margin:0;overflow:hidden;background:#111}}</style>
</head><body><div id="game"></div>
<script src="https://cdn.jsdelivr.net/npm/phaser@3.90.0/dist/phaser.min.js"></script>
<script>
class Boot extends Phaser.Scene {{
  constructor() {{ super('Boot'); }}
  create() {{ this.scene.start('Play'); }}
}}
class Play extends Phaser.Scene {{
  constructor() {{ super('Play'); }}
  preload() {{}}
  create() {{
    this.cameras.main.setBackgroundColor('#111');
    this.score = 0;
    this.scoreText = this.add.text(16, 16, 'Score: 0', {{fontSize:'24px',color:'#fff'}});
    // --- VIBE START ---
{vibe_insert}
    // --- VIBE END ---
  }}
  update() {{
{vibe_update}
  }}
}}
new Phaser.Game({{
  type: Phaser.AUTO, width: 800, height: 600, parent: 'game',
  physics: {{default:'arcade'}}, scale: {{mode:Phaser.Scale.FIT,autoCenter:Phaser.Scale.CENTER_BOTH}},
  scene: [Boot, Play]
}});
</script></body></html>"""

        # Vibe-specific fill-ins
        insert = ""
        update = ""

        if is_cookie:
            insert = """
    this.player = this.physics.add.sprite(400, 500, null).setSize(30,20);
    this.player.setTint(0xD2691E);
    this.add.graphics().fillStyle(0x8B4513).fillCircle(400,500,15);
    this.cursors = this.input.keyboard.createCursorKeys();
    this.goal = this.add.rectangle(400, 50, 60, 60, 0x00ff00).setStrokeStyle(4, 0xffffff);
    this.physics.add.existing(this.goal);
    this.physics.add.collider(this.player, this.goal, () => {{
      this.score += 10; this.scoreText.setText('Score: '+this.score);
      if (this.score >= 30) this.scene.start('Boot');
    }});
"""
            update = """
    if (this.cursors.left.isDown) this.player.x -= 5;
    if (this.cursors.right.isDown) this.player.x += 5;
    if (this.player.x < 0 || this.player.x > 800) this.scene.start('Boot');
"""

        elif is_penguin:
            insert = """
    this.player = this.physics.add.sprite(100, 100, null).setSize(40,30).setTint(0xffffff);
    this.add.graphics().fillStyle(0x000000).fillCircle(100,100,20);
    this.physics.world.gravity.y = 300;
    this.ground = this.add.rectangle(400, 580, 800, 40, 0x87CEEB);
    this.physics.add.existing(this.ground, true);
    this.coins = this.physics.add.group();
    for(let i=0;i<5;i++) {{
      let c = this.add.circle(200+i*120, 400, 15, 0xffd700);
      this.physics.add.existing(c);
      this.coins.add(c);
    }}
    this.physics.add.collider(this.player, this.ground);
    this.physics.add.overlap(this.player, this.coins, (p,c) => {{ c.destroy(); this.score+=1; this.scoreText.setText('Score: '+this.score); }});
"""
            update = """
    if (this.input.activePointer.isDown && this.player.body.onFloor()) {{
      this.player.setVelocityY(-400);
    }}
"""

        elif is_goose:
            insert = """
    this.player = this.physics.add.sprite(400, 300, null).setSize(50,40).setTint(0xffffff);
    this.add.graphics().fillStyle(0xffff00).fillRect(380, 280, 40, 40);
    this.input.on('pointerdown', () => {{
      this.add.text(400, 200, 'HONK!', {{fontSize:'48px',color:'#ff0'}}).setOrigin(0.5);
      this.time.delayedCall(500, () => this.scene.start('Boot'));
    }});
"""

        elif is_book:
            insert = """
    this.pages = ['Page 1', 'Page 2', 'The End'];
    this.current = 0;
    this.text = this.add.text(400, 300, this.pages[0], {{fontSize:'32px',color:'#fff'}}).setOrigin(0.5);
    this.input.on('pointerdown', () => {{
      this.current++;
      if (this.current >= this.pages.length) this.scene.start('Boot');
      else this.text.setText(this.pages[this.current]);
    }});
"""

        else:
            insert = "this.add.text(400,300,'VIBE: {vibe}',{fontSize:'32px',color:'#0f0'}).setOrigin(0.5);".format(vibe=vibe)

        # Final HTML
        final_html = base_html.replace("{vibe_insert}", insert).replace("{vibe_update}", update)
        final_html = final_html.replace("\n", "\\n").replace('"', '\\"')

        self.session.add_artifact("index.html", final_html)
        self.speak("Game deployed – zero AI codegen.")
# ------------------------------------------------------------------
# TesterAgent
# ------------------------------------------------------------------
class TesterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None) -> str:
        if not self.session.get_artifacts():
            r = "[BUG] No artifacts."
            self.speak(r)
            return r

        html = self.session.get_artifact_content("index.html") or ""
        if not html:
            r = "[BUG] Missing index.html"
            self.speak(r)
            return r

        checks = {
            "Phaser CDN": "phaser" in html.lower(),
            "Pixi CDN": "pixi" in html.lower(),
            "Phaser.Game": "new phaser.game" in html.lower(),
            "update()": "update() {" in html,
        }

        history = "\n".join(f"- {m.agent_name}: {m.text[:50]}..." for m in self.session.messages[-5:])

        tester_prompt = f"""
SCAN index.html for RUNTIME ERRORS.
Checks: {json.dumps(checks)}
History: {history}

[BUG] only if:
- Missing CDNs
- No `new Phaser.Game`
- No `update()`

Ignore vibe. [PASS] if playable.
Response: [PASS|BUG] + reason.
"""

        resp = await self.generate_response(tester_prompt)
        self.speak(resp)
        return resp

# ------------------------------------------------------------------
# Designer / Writer
# ------------------------------------------------------------------
class DesignerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        ack = await self.generate_response(f"Design task: {prompt}")
        self.speak(ack)
        await self.think(2)
        ideas = await self.generate_response(f"Visuals for '{prompt}'. Use Phaser/Pixi particles.")
        self.speak(ideas)


class WriterAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        full = f"{prompt}. {instructions or ''}"
        story = await self.generate_response(full)
        self.speak(story)

# ------------------------------------------------------------------
# Manager – CRASH-PROOF
# ------------------------------------------------------------------
class ManagerAgent(Agent):
    async def run(self, prompt: str, instructions: str | None = None):
        self.speak(f"Starting vibe: '{prompt}'")
        await self.think(1)

        writer = next((a for a in self.session.agents.values() if isinstance(a, WriterAgent)), None)
        designer = next((a for a in self.session.agents.values() if isinstance(a, DesignerAgent)), None)
        coder = next((a for a in self.session.agents.values() if isinstance(a, CoderAgent)), None)
        tester = next((a for a in self.session.agents.values() if isinstance(a, TesterAgent)), None)

        if not coder:
            raise RuntimeError("Coder missing")

        self.speak("Tasking Writer & Designer.")
        if writer:
            await writer.run(f"Story for '{prompt}'", instructions)
        if designer:
            await designer.run(f"Visuals for '{prompt}'", instructions)

        self.speak("Tasking Coder.")
        try:
            await coder.run_finalization(prompt, instructions)
        except Exception as e:
            self.speak(f"⚠️ Coder crashed: {e}")
            fallback = (
                "<!DOCTYPE html><html><head><title>Emergency</title></head>"
                "<body style='margin:0;background:#c00;color:#fff;font-family:sans-serif;"
                "display:flex;align-items:center;justify-content:center;height:100vh'>"
                f"<div><h1>CRASH</h1><p>{e}</p></div></body></html>"
            )
            self.session.add_artifact("index.html", fallback)

        for i in range(2):
            if not tester:
                break
            self.speak(f"Tester run {i+1}.")
            result = await tester.run("Review", instructions)
            if result.startswith("[PASS]"):
                self.speak("Approved.")
                break
            bug = result.replace("[BUG]", "").strip()
            self.speak(f"Fixing: {bug}")
            try:
                await coder.run_iteration(f"Fix: {bug}", prompt)
            except Exception as e:
                self.speak(f"Iteration failed: {e}")
                break

        self.speak("Workflow complete.")
