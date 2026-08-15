/* シールノートの最小限JS（要件11章：削除確認とService Workerのみ + まとめの演出）。 */
(function () {
  "use strict";

  // JSが動いていることを示す（CSSのフォールバック解除用）
  document.documentElement.classList.remove("no-js");

  // --- 削除確認ダイアログ（F-04） ---
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      var message = form.getAttribute("data-confirm") || "削除しますか？";
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // --- あいことばの表示切り替え ---
  document.querySelectorAll("[data-pw-toggle]").forEach(function (button) {
    var input = button.parentNode.querySelector("input");
    if (!input) return;
    button.addEventListener("click", function () {
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      button.setAttribute("aria-pressed", show ? "true" : "false");
      button.setAttribute(
        "aria-label",
        show ? "あいことばを隠す" : "あいことばを表示する"
      );
      input.focus();
    });
  });

  // --- まとめ画面の演出（唯一の動き・要件9章） ---
  // prefers-reduced-motion でも data-revealed は付けるが、CSS側でアニメを止める。
  if (document.querySelector("[data-reveal]")) {
    // 次フレームで付与し、初期状態→表示のトランジションを確実に起こす
    requestAnimationFrame(function () {
      document.body.setAttribute("data-revealed", "");
    });
  }

  // --- Service Worker 登録（要件14章） ---
  // 静的ホスティング下では sw.js のスコープは /static/ に限定される。
  // 本SWは静的ファイルのキャッシュのみを行い、HTMLは扱わないため、これで十分。
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker
        .register("/static/sw.js")
        .catch(function () {
          /* 登録失敗は無視（アプリの動作には影響しない） */
        });
    });
  }
})();
