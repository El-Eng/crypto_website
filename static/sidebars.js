/* global bootstrap: false */
// (function () {
//   'use strict'
//   var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
//   tooltipTriggerList.forEach(function (tooltipTriggerEl) {
//     new bootstrap.Tooltip(tooltipTriggerEl)
//   })
// })()

var sidebarmini = true;

function toggleSidebar() {
  if (sidebarmini) {
    console.log("hovering");
    document.getElementById("sidebar").style.width = "320px";

    //document.getElementById("dim").style.width = "calc(100% - 300px)";
    //document.getElementById("dim").style.zIndex = "3";

    document.getElementById("dim").style.KhtmlOpacity = ".5";
    document.getElementById("dim").style.MozOpacity = ".5";
    document.getElementById("dim").style.opacity = ".55";
    document.getElementById("dim").style.filter  = 'alpha(opacity=50)'

    //document.getElementById("main").style.marginLeft = "300px";
    this.sidebarmini = false;
  } else {
    console.log("hovering");
    document.getElementById("sidebar").style.width = "60px";

    //document.getElementById("dim").style.width = "calc(100% - 60px)";
    //document.getElementById("dim").style.zIndex = "-5";

    document.getElementById("dim").style.KhtmlOpacity = "0";
    document.getElementById("dim").style.MozOpacity = "0";
    document.getElementById("dim").style.opacity = "0";
    document.getElementById("dim").style.filter  = 'alpha(opacity=0)'

    //document.getElementById("main").style.marginLeft = "60px";
    this.sidebarmini = true;
  }
}

