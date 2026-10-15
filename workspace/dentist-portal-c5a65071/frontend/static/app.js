// Small progressive-enhancement script: mobile nav toggle and client-side
// validation for the appointment form. Server-side validation remains the
// source of truth, so the form still works without JavaScript.
(function () {
  "use strict";

  var toggle = document.getElementById("navToggle");
  var nav = document.getElementById("siteNav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
    nav.addEventListener("click", function (event) {
      if (event.target.tagName === "A") {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  var form = document.getElementById("appointmentForm");
  if (!form) {
    return;
  }

  function showError(field, message) {
    var existing = field.parentNode.querySelector(".field-error");
    if (existing) {
      existing.remove();
    }
    if (!message) {
      return;
    }
    var note = document.createElement("p");
    note.className = "field-error";
    note.textContent = message;
    field.parentNode.appendChild(note);
  }

  function isValidEmail(value) {
    var at = value.indexOf("@");
    if (at < 1) {
      return false;
    }
    var domain = value.slice(at + 1);
    return domain.indexOf(".") > 0 && !domain.endsWith(".");
  }

  form.addEventListener("submit", function (event) {
    var valid = true;
    var name = form.elements.name;
    var email = form.elements.email;
    var phone = form.elements.phone;
    var date = form.elements.preferred_date;

    showError(name, "");
    showError(email, "");
    showError(phone, "");
    showError(date, "");

    if (!name.value.trim()) {
      showError(name, "Please enter your name.");
      valid = false;
    }
    if (!isValidEmail(email.value.trim())) {
      showError(email, "Please enter a valid email address.");
      valid = false;
    }
    if (!phone.value.trim()) {
      showError(phone, "Please enter a phone number.");
      valid = false;
    }
    if (!date.value.trim()) {
      showError(date, "Please choose a preferred date.");
      valid = false;
    }

    if (!valid) {
      event.preventDefault();
    }
  });
})();
