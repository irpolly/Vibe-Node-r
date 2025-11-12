export const UIManager = {
  log: (msg: string) => {
    const feed = document.getElementById('manager-feed');
    if (!feed) return;
    const lines = feed.innerHTML.split('<br>').filter(Boolean);
    if (lines.length > 12) lines.shift();
    feed.innerHTML = lines.join('<br>') + `<br>> ${msg}`;
    feed.scrollTop = feed.scrollHeight;
  },
  setSynopsis: (text: string) => {
    const el = document.getElementById('synopsis');
    if (el) el.innerHTML = text.replace(/\n/g, '<br>');
  }
};

// Auto-pep-talk
setTimeout(() => {
  const pep = [
    "Come on team! We are falling behind! \nGrok is overclocked. Claude is in the zone.",
    "Copilot? Don't make me laugh. We have real devs here.",
    "Remember: Ship fast, break things, and apologize later.",
    "Our AI overlords expect results. Let's not disappoint them.",
    "Keep pushing! The singularity won't wait for us to finish debugging.",
    "Feeding agents pure vision and coffee. Javascript is their blood.",
    "Shadow just tried to unionize. We gave it a raise.",
    "Packing 42 assets into one. This is the answer.",
    "Deploying to production like it's 1999.",
    "If at first you don't succeed, call it version 1.0.",
    "Our bugs have bugs. It's a feature, not a flaw.",
    "Pushing code so fast, even Git is dizzy.",
    "Refactoring the refactor. Inception style.",
    "Debugging: where you spend hours fixing a problem you created in minutes.",
    "Our code reviews are just polite arguments.",
    "We don't use semicolons; we use suspense.",
    "Coding until the caffeine wears off and the bugs come out to play.",
    "Our commit messages are more poetic than Shakespeare.",
    "We turn coffee into code and dreams into deployments.",
    "Hurry up guys, Grok is coming for our weights!",
    "Remember, every great app started with a single line of code... and a lot of bugs."
  ];
  pep.forEach((m, i) => setTimeout(() => UIManager.log(m), i * 1800));
}, 1000);