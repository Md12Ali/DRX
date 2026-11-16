/* ==========================================================================
   DRX - front-end behaviour
   Progressive enhancement: every page also works without JavaScript.
   ========================================================================== */

/* jshint esversion: 11, browser: true */

(function () {
  "use strict";

  const messageArea = document.getElementById("messages");

  /**
   * Show a feedback message in the same style as Django's messages.
   * Uses textContent (never innerHTML) so it can't inject markup.
   */
  function showMessage(text, level) {
    if (!messageArea) {
      return;
    }
    const wrapper = document.createElement("div");
    wrapper.className = "message message-" + (level || "info");
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    const close = document.createElement("button");
    close.type = "button";
    close.className = "message-close";
    close.setAttribute("aria-label", "Dismiss message");
    close.textContent = "×";
    wrapper.append(paragraph, close);
    messageArea.appendChild(wrapper);
  }

  /* Mobile navigation
     ------------------------------------------------------------------------ */
  function initNavToggle() {
    const toggle = document.querySelector(".nav-toggle");
    const menu = document.getElementById("nav-menu");
    if (!toggle || !menu) {
      return;
    }
    toggle.addEventListener("click", function () {
      const isOpen = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!isOpen));
      toggle.querySelector(".visually-hidden").textContent = isOpen ? "Open menu" : "Close menu";
      menu.classList.toggle("is-open", !isOpen);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && menu.classList.contains("is-open")) {
        toggle.click();
        toggle.focus();
      }
    });
  }

  /* Dismissable messages
     ------------------------------------------------------------------------ */
  function initMessageDismiss() {
    if (!messageArea) {
      return;
    }
    messageArea.addEventListener("click", function (event) {
      if (event.target.classList.contains("message-close")) {
        event.target.closest(".message").remove();
      }
    });
  }

  /* Character counters for textareas with data-max-length
     ------------------------------------------------------------------------ */
  function initCharCounters() {
    document.querySelectorAll("textarea[data-max-length]").forEach(function (textarea) {
      const max = parseInt(textarea.dataset.maxLength, 10);
      const counter = document.createElement("p");
      counter.className = "char-counter";
      counter.setAttribute("aria-live", "polite");
      textarea.insertAdjacentElement("afterend", counter);

      function update() {
        const remaining = max - textarea.value.length;
        counter.textContent = remaining + " characters left";
        counter.classList.toggle("is-near-limit", remaining <= Math.max(20, max * 0.1));
      }
      textarea.addEventListener("input", update);
      update();
    });
  }

  /* Image preview for file inputs with data-preview="<img id>"
     ------------------------------------------------------------------------ */
  function initImagePreviews() {
    document.querySelectorAll("input[type=file][data-preview]").forEach(function (input) {
      const preview = document.getElementById(input.dataset.preview);
      if (!preview) {
        return;
      }
      input.addEventListener("change", function () {
        const file = input.files && input.files[0];
        if (!file || !file.type.startsWith("image/")) {
          if (file) {
            showMessage("That file isn't an image. Please choose a JPG, PNG or WebP.", "error");
            input.value = "";
          }
          preview.hidden = true;
          return;
        }
        preview.src = URL.createObjectURL(file);
        preview.hidden = false;
      });
    });
  }

  /* Loading text on submit, so users know something is happening
     ------------------------------------------------------------------------ */
  function initLoadingButtons() {
    document.querySelectorAll("form[data-loading-text]").forEach(function (form) {
      form.addEventListener("submit", function () {
        const button = form.querySelector("button[type=submit]");
        if (!button) {
          return;
        }
        button.setAttribute("aria-busy", "true");
        button.textContent = form.dataset.loadingText;
        window.setTimeout(function () {
          button.disabled = true;
        }, 0);
      });
    });
    // Coming back with the Back button restores a fresh page.
    window.addEventListener("pageshow", function (event) {
      if (event.persisted) {
        window.location.reload();
      }
    });
  }

  /* Confirmation for instructor-only destructive buttons
     ------------------------------------------------------------------------ */
  function initConfirmForms() {
    document.querySelectorAll("form.js-confirm-form").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        if (!window.confirm(form.dataset.confirm)) {
          event.preventDefault();
        }
      });
    });
  }

  /* Booking form: live free time slots
     ------------------------------------------------------------------------ */
  function initSlotPicker() {
    const form = document.querySelector(".booking-form");
    const dateInput = document.querySelector(".js-booking-date");
    const timeInput = document.querySelector(".js-booking-time");
    const picker = document.getElementById("slot-picker");
    if (!form || !dateInput || !timeInput || !picker) {
      return;
    }
    const grid = picker.querySelector(".slot-grid");
    const status = picker.querySelector(".slot-status");
    const baseUrl = dateInput.dataset.availabilityUrl;

    function currentDuration() {
      const checked = form.querySelector("input[name=duration_minutes]:checked");
      return checked ? checked.value : "60";
    }

    function selectSlot(button) {
      grid.querySelectorAll(".slot-button").forEach(function (other) {
        other.setAttribute("aria-pressed", "false");
      });
      button.setAttribute("aria-pressed", "true");
      timeInput.value = button.dataset.time;
    }

    function renderSlots(times) {
      grid.replaceChildren();
      times.forEach(function (time) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "slot-button";
        button.dataset.time = time;
        button.textContent = time;
        button.setAttribute("aria-pressed", String(time === timeInput.value));
        button.addEventListener("click", function () {
          selectSlot(button);
        });
        grid.appendChild(button);
      });
    }

    function loadSlots() {
      if (!dateInput.value) {
        picker.hidden = true;
        return;
      }
      picker.hidden = false;
      status.textContent = "Checking availability…";
      grid.replaceChildren();

      const params = new URLSearchParams({ date: dateInput.value, duration: currentDuration() });
      if (form.dataset.bookingId) {
        params.set("booking", form.dataset.bookingId);
      }

      fetch(baseUrl + "?" + params.toString(), { headers: { Accept: "application/json" } })
        .then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) {
              throw new Error(data.error || "Couldn't load times.");
            }
            return data;
          });
        })
        .then(function (data) {
          renderSlots(data.times);
          if (!data.works_that_day) {
            status.textContent = "Your instructor doesn't teach on this day. Please pick another date.";
          } else if (data.times.length === 0) {
            status.textContent = "No free times on this day. Please try another date.";
          } else {
            status.textContent = data.times.length + " free start time" +
              (data.times.length === 1 ? "" : "s") + ". Pick one, or type a time below.";
          }
        })
        .catch(function (error) {
          status.textContent = error.message + " You can still type a time below.";
        });
    }

    dateInput.addEventListener("change", loadSlots);
    form.querySelectorAll("input[name=duration_minutes]").forEach(function (radio) {
      radio.addEventListener("change", loadSlots);
    });
    loadSlots();
  }

  /* Checkout: countdown for the slot hold
     ------------------------------------------------------------------------ */
  function initHoldCountdown() {
    const timer = document.querySelector(".hold-timer");
    if (!timer) {
      return;
    }
    const output = timer.querySelector(".js-countdown");
    const expires = new Date(timer.dataset.expires).getTime();

    function tick() {
      const seconds = Math.max(0, Math.round((expires - Date.now()) / 1000));
      if (seconds === 0) {
        output.textContent = "Time's up. Reload the page to book again.";
        return;
      }
      const minutes = Math.floor(seconds / 60);
      output.textContent = "(" + minutes + " min " + String(seconds % 60).padStart(2, "0") + " s left)";
      window.setTimeout(tick, 1000);
    }
    tick();
  }

  /* Home page: "Do you cover my postcode?" without reloading
     ------------------------------------------------------------------------ */
  function initPostcodeCheck() {
    const form = document.querySelector(".js-postcode-check");
    const output = document.querySelector(".js-postcode-result");
    if (!form || !output) {
      return;
    }
    form.addEventListener("submit", function (event) {
      const value = form.elements.postcode.value.trim();
      if (!value) {
        return;
      }
      event.preventDefault();
      const params = new URLSearchParams({ postcode: value });

      fetch(form.dataset.checkUrl + "?" + params.toString(), { headers: { Accept: "application/json" } })
        .then(function (response) {
          return response.json();
        })
        .then(function (data) {
          const result = document.createElement("p");
          if (!data.valid) {
            result.className = "result-no";
            result.textContent = "That doesn't look like a UK postcode. Try something like E3 5AA.";
          } else if (data.covered) {
            result.className = "result-yes";
            result.textContent = "Yes! " + data.postcode + " is in " + data.district + " (" + data.areas + "). ";
            const link = document.createElement("a");
            link.href = form.dataset.bookUrl;
            link.textContent = "Book a lesson";
            result.appendChild(link);
          } else {
            result.className = "result-no";
            result.textContent = "Sorry, " + data.postcode + " (" + data.district + ") is outside the area I cover. " +
              "You could choose a pick-up point in a covered area, like your school or work.";
          }
          output.replaceChildren(result);
        })
        .catch(function () {
          form.submit();
        });
    });
  }

  /* Dashboard score ring
     ------------------------------------------------------------------------ */
  function initScoreRings() {
    document.querySelectorAll(".score-ring[data-percent]").forEach(function (ring) {
      ring.style.setProperty("--p", ring.dataset.percent);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNavToggle();
    initMessageDismiss();
    initCharCounters();
    initImagePreviews();
    initLoadingButtons();
    initConfirmForms();
    initSlotPicker();
    initHoldCountdown();
    initPostcodeCheck();
    initScoreRings();
  });
})();
