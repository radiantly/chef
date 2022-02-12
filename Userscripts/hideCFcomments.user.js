// ==UserScript==
// @name         Hide Codeforces comments
// @namespace    LB.HCC
// @version      2.1
// @description  This nifty userscript allows you to hide CF comments
// @author       radiantly
// @match        *://codeforces.com/blog/entry/*
// @run-at       document-end
// @grant        GM_addStyle
// ==/UserScript==

(function () {
  "use strict";

  GM_addStyle(`
.lb-hidden-comment .avatar > a,
.lb-hidden-comment .comment-content,
.lb-hidden-comment .reply.info,
.lb-hidden-comment .bad-comment-replacement,
.lb-hidden-comment-tree + .comment-children,
.lb-hidden-comment .lb-tree {
  display: none;
}
.lb-tree {
  cursor: pointer;
  text-decoration: underline;
}
.lb-main-btn::before {
  content: "Hide";
  cursor: pointer;
  text-decoration: underline;
}
.lb-hidden-comment .lb-main-btn::before {
  content: "Show";
}
.lb-hidden-comment-tree .lb-main-btn::before {
  content: "Show tree";
}
`);

  const comments = Array.from(
    document.querySelectorAll(".comment-table .right .info .item:first-child")
  );

  const blogId = location.pathname.replace(/^.*\//, "");

  const keyName = `lb-${blogId}`;

  const stored = localStorage.getItem(keyName);
  const storedObj = stored
    ? JSON.parse(stored, (key, val) =>
        Array.isArray(val) ? new Set(val) : val
      )
    : {
        comments: new Set(),
        trees: new Set(),
      };

  const allCommentElems = Array.from(
    document.querySelectorAll(".comment > table.comment-table")
  );
  for (const cElem of allCommentElems) {
    const commentId = cElem.getAttribute("commentid");
    if (!commentId) continue;
    if (storedObj.trees.has(commentId)) {
      cElem.classList.add("lb-hidden-comment", "lb-hidden-comment-tree");
    } else if (storedObj.comments.has(commentId)) {
      cElem.classList.add("lb-hidden-comment");
    }
  }

  const updateLocalStorage = () =>
    localStorage.setItem(
      keyName,
      JSON.stringify(storedObj, (key, val) =>
        val instanceof Set ? Array.from(val) : val
      )
    );

  const handleClick = (e) => {
    const getCommentElem = (elem) =>
      (elem.getAttribute("commentid") && elem) ||
      getCommentElem(elem.parentNode);

    const commentElem = getCommentElem(e.target);
    const commentId = commentElem.getAttribute("commentid");
    commentElem.classList.toggle("lb-hidden-comment");
    if (e.target.classList.contains("lb-tree")) {
      commentElem.classList.add("lb-hidden-comment-tree");
      storedObj.trees.add(commentId);
    } else if (!commentElem.classList.contains("lb-hidden-comment")) {
      commentElem.classList.remove("lb-hidden-comment-tree");
      storedObj.comments.delete(commentId);
      storedObj.trees.delete(commentId);
    } else {
      storedObj.comments.add(commentId);
    }
    updateLocalStorage();
  };

  for (const comment of comments) {
    const itemSpan = document.createElement("span");
    itemSpan.classList.add(
      "item",
      "lb-clickable",
      "lb-hide-btn",
      "lb-main-btn"
    );
    itemSpan.addEventListener("click", handleClick);
    const itemSpanTree = document.createElement("span");
    itemSpanTree.classList.add("item", "lb-clickable", "lb-tree");
    itemSpanTree.innerText = "tree";
    itemSpanTree.addEventListener("click", handleClick);
    comment.insertAdjacentElement("afterend", itemSpanTree);
    comment.insertAdjacentElement("afterend", itemSpan);
  }
})();
