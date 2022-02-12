// ==UserScript==
// @name        Suppress Confirmation
// @namespace   LB.SC
// @match       https://www.codechef.com/*
// @grant       none
// @version     1.1
// @author      radiantly
// @description Suppresses the confirmation dialog when submitting code on codechef
// ==/UserScript==

window.confirm = () => true;
