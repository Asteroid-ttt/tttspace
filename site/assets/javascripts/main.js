document.addEventListener("DOMContentLoaded", () => {
  const pathname = window.location.pathname;
  const segments = pathname.split("/").filter(Boolean);
  const isHomeByPath = segments.length === 0 || (segments.length === 1 && segments[0] === "index.html");
  const isHomeByContent = document.querySelector(".ttt-homepage") !== null;
  if (isHomeByPath || isHomeByContent) {
    document.body.classList.add("ttt-home");
  }

  // Hide right sidebar if TOC is empty
  const tocList = document.querySelector(".md-sidebar--secondary .md-nav__list");
  if (!tocList || tocList.children.length === 0) {
    const secondary = document.querySelector(".md-sidebar--secondary");
    if (secondary) secondary.style.display = "none";
  }

  const cards = document.querySelectorAll(".md-content__inner > h2, .md-content__inner > h3");
  cards.forEach((node, idx) => {
    node.style.opacity = "0";
    node.style.transform = "translateY(8px)";
    setTimeout(() => {
      node.style.transition = "opacity .28s ease, transform .28s ease";
      node.style.opacity = "1";
      node.style.transform = "translateY(0)";
    }, 80 + idx * 35);
  });

  const firstSeg = segments[0] || "";
  const primary = document.querySelector(".md-sidebar--primary .md-nav--primary > .md-nav__list");
  if (!primary) return;

  const topItems = Array.from(primary.children).filter((el) => el.classList.contains("md-nav__item"));
  let currentTopItem = null;

  topItems.forEach((item) => {
    const link = item.querySelector(":scope > .md-nav__link");
    const href = link ? link.getAttribute("href") || "" : "";
    const isHome = href === "." || href === "./" || href === "/";
    const isCurrent = firstSeg && (href.includes(`/${firstSeg}/`) || href.startsWith(`${firstSeg}/`));

    if (isCurrent || item.classList.contains("md-nav__item--active")) {
      currentTopItem = item;
      return;
    }
    if (!isHome) {
      item.classList.add("ttt-nav-hidden");
    }
  });

  // Collapse/expand is handled by Material's native nav toggles.
});
