// One click on the "Generate Executive Summary" button in the message box runs it.
// Chainlit command buttons normally wait for the send button; when the text box is
// empty we press send for the user. With text typed, the command goes with it.
(function () {
  var ONE_CLICK = ["command-Generate Executive Summary"];

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
