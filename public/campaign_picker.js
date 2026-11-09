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
