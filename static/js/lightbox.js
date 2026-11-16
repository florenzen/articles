(function () {
  var dialog = document.querySelector("dialog.lightbox");
  var images = Array.prototype.slice.call(
    document.querySelectorAll("article img"),
  );
  if (!dialog || images.length === 0) return;

  var view = dialog.querySelector(".lightbox-image");
  var caption = dialog.querySelector(".lightbox-caption");
  var counter = dialog.querySelector(".lightbox-counter");
  var current = 0;

  if (images.length < 2) dialog.classList.add("single");

  images.forEach(function (img, i) {
    var wrapper = document.createElement("span");
    wrapper.className = "zoom";
    img.parentNode.insertBefore(wrapper, img);
    wrapper.appendChild(img);

    var button = document.createElement("button");
    button.type = "button";
    button.className = "zoom-button";
    button.setAttribute("aria-label", dialog.dataset.enlarge);
    button.title = dialog.dataset.enlarge;
    button.innerHTML = '<span class="icon icon-enlarge"></span>';
    button.addEventListener("click", function () {
      open(i);
    });
    wrapper.appendChild(button);

    img.addEventListener("click", function () {
      open(i);
    });
  });

  function show(i) {
    current = (i + images.length) % images.length;
    var img = images[current];
    view.src = img.currentSrc || img.src;
    view.alt = img.alt;
    caption.textContent = img.alt;
    counter.textContent = current + 1 + " / " + images.length;
  }

  function open(i) {
    show(i);
    dialog.showModal();
  }

  dialog.querySelector(".lightbox-prev").addEventListener("click", function () {
    show(current - 1);
  });
  dialog.querySelector(".lightbox-next").addEventListener("click", function () {
    show(current + 1);
  });
  dialog
    .querySelector(".lightbox-close")
    .addEventListener("click", function () {
      dialog.close();
    });

  dialog.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") {
      show(current - 1);
      e.preventDefault();
    } else if (e.key === "ArrowRight") {
      show(current + 1);
      e.preventDefault();
    }
  });

  dialog.addEventListener("click", function (e) {
    if (e.target === dialog || e.target.classList.contains("lightbox-stage"))
      dialog.close();
  });

  var touchX = null;
  dialog.addEventListener(
    "touchstart",
    function (e) {
      touchX = e.touches[0].clientX;
    },
    { passive: true },
  );
  dialog.addEventListener("touchend", function (e) {
    if (touchX === null) return;
    var dx = e.changedTouches[0].clientX - touchX;
    touchX = null;
    if (Math.abs(dx) > 50) show(current + (dx < 0 ? 1 : -1));
  });
})();
