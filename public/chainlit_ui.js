// Tell the server as soon as the Campaign picker in the message box changes.
// Buttons (examples, executive summary) don't carry the picker value, so without
// this they would use the previously active campaign until the next typed message.
// Chainlit forwards window messages to the server (@cl.on_window_message).
(function () {
  var TRIGGER_ID = "mode-picker-trigger-campaign";
  var CAMPAIGN_ID = /CMP-\d{4}-\d{3}/;
  var lastSent = null;

  function report() {
    var trigger = document.getElementById(TRIGGER_ID);
    if (!trigger) return;
    var match = (trigger.textContent || "").match(CAMPAIGN_ID);
    if (!match || match[0] === lastSent) return;
    lastSent = match[0];
    window.postMessage({ type: "campaign_picked", campaign_id: match[0] }, window.location.origin);
  }

  new MutationObserver(report).observe(document.documentElement, {
    childList: true,
    subtree: true,
    characterData: true,
  });
})();

// One click on a message-box button (Executive summary, Refresh data) runs it.
// Chainlit commands normally wait for the send button; when the text box is
// empty we press send for the user. With text typed, the command goes with it.
(function () {
  var ONE_CLICK = ["command-Executive summary", "command-Refresh data"];

  document.addEventListener("click", function (event) {
    var button = event.target.closest && event.target.closest("button.command-button");
    if (!button || ONE_CLICK.indexOf(button.id) === -1) return;
    var input = document.getElementById("chat-input");
    var typed = input ? (input.value !== undefined ? input.value : input.textContent) : "";
    if ((typed || "").trim()) return;
    setTimeout(function () {
      var send = document.getElementById("chat-submit");
      if (send && !send.disabled) send.click();
    }, 50);
  });
})();
