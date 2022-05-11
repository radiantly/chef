// ==UserScript==
// @name        Multi-cursor select
// @namespace   LB
// @match       https://leetcode.com/*problems/*/
// @grant       none
// @version     1.0
// @author      radiantly
// @description Adds multicursor select to the code editor in leetcode
// ==/UserScript==

// Node that will be observed for mutations
const targetNode =
  document.getElementById("app") ||
  document.getElementById("submission-form-app");

// Options for the observer (which mutations to observe)
const config = { attributes: true, childList: true, subtree: false };

const observer = new MutationObserver((mutationsList, observer) => {
  setTimeout(
    () =>
      document
        .querySelector(".CodeMirror")
        .CodeMirror.addKeyMap({ "Ctrl-D": "selectNextOccurrence" }),
    2000
  );
  observer.disconnect();
});

// Start observing the target node for configured mutations
observer.observe(targetNode, config);
