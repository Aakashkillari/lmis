import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import Lenis from "lenis";
import { usePrefs } from "../prefs";

const reducedSystem = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const finePointer = () => window.matchMedia("(pointer: fine)").matches;

type ScrollState = { y: number; max: number };
const listeners = new Set<(s: ScrollState) => void>();
let lenisRef: Lenis | null = null;

const emit = () => {
  const y = lenisRef ? lenisRef.scroll : window.scrollY;
  const max = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
  listeners.forEach((fn) => fn({ y, max }));
};

export function useScroll() {
  const [state, setState] = useState<ScrollState>({ y: 0, max: 1 });
  useEffect(() => {
    listeners.add(setState);
    emit();
    return () => { listeners.delete(setState); };
  }, []);
  return state;
}

export function scrollToY(y: number, immediate = false) {
  if (lenisRef) lenisRef.scrollTo(y, { immediate });
  else window.scrollTo({ top: y, behavior: immediate ? "auto" : "smooth" });
}

export function SmoothScroll() {
  const location = useLocation();
  const [prefs] = usePrefs();
  const motion = prefs.motion && !reducedSystem();

  useEffect(() => {
    const onNative = () => emit();
    window.addEventListener("scroll", onNative, { passive: true });
    window.addEventListener("resize", onNative);
    if (!prefs.smooth || !motion) return () => { window.removeEventListener("scroll", onNative); window.removeEventListener("resize", onNative); };
    const instance = new Lenis({ lerp: 0.11, smoothWheel: true, wheelMultiplier: 1, autoRaf: true });
    lenisRef = instance;
    instance.on("scroll", emit);
    return () => {
      instance.destroy();
      lenisRef = null;
      window.removeEventListener("scroll", onNative);
      window.removeEventListener("resize", onNative);
    };
  }, [prefs.smooth, motion]);

  useEffect(() => {
    scrollToY(0, true);
    const t = window.setTimeout(emit, 300);
    return () => window.clearTimeout(t);
  }, [location.pathname]);

  useEffect(() => {
    const items = () => Array.from(document.querySelectorAll<HTMLElement>("[data-reveal]:not(.in)"));
    if (!motion || !("IntersectionObserver" in window)) {
      const all = () => items().forEach((el) => el.classList.add("in"));
      all();
      const mutation = new MutationObserver(all);
      mutation.observe(document.body, { childList: true, subtree: true });
      return () => mutation.disconnect();
    }
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { entry.target.classList.add("in"); observer.unobserve(entry.target); }
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.05 });
    const watch = () => items().forEach((el) => observer.observe(el));
    watch();
    const mutation = new MutationObserver(watch);
    mutation.observe(document.body, { childList: true, subtree: true });
    const safety = window.setTimeout(() => {
      items().forEach((el) => { if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add("in"); });
    }, 900);
    return () => { observer.disconnect(); mutation.disconnect(); window.clearTimeout(safety); };
  }, [location.pathname, motion]);

  return null;
}

export function Scroller() {
  const { y, max } = useScroll();
  const [active, setActive] = useState(false);
  const [drag, setDrag] = useState(false);
  const hide = useRef(0);
  const track = useRef<HTMLDivElement>(null);
  const viewport = typeof window === "undefined" ? 800 : window.innerHeight;
  const contentHeight = max + viewport;
  const thumb = Math.max(44, (viewport / contentHeight) * (viewport - 24));
  const travel = viewport - 24 - thumb;
  const top = max > 0 ? (y / max) * travel : 0;

  useEffect(() => {
    setActive(true);
    window.clearTimeout(hide.current);
    hide.current = window.setTimeout(() => setActive(false), 1100);
  }, [y]);

  useEffect(() => {
    if (!drag) return;
    const move = (e: PointerEvent) => {
      const box = track.current?.getBoundingClientRect();
      if (!box) return;
      const ratio = Math.min(1, Math.max(0, (e.clientY - box.top - thumb / 2) / (box.height - thumb)));
      scrollToY(ratio * max, true);
    };
    const up = () => setDrag(false);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    return () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
  }, [drag, max, thumb]);

  if (max <= 4) return null;
  return (
    <div ref={track} className={`scroller ${active || drag ? "on" : ""}`} aria-hidden="true"
      onPointerDown={(e) => {
        if ((e.target as HTMLElement).classList.contains("thumb")) { setDrag(true); return; }
        const box = track.current!.getBoundingClientRect();
        scrollToY(((e.clientY - box.top) / box.height) * max);
      }}>
      <div className="thumb" style={{ height: thumb, transform: `translate3d(0, ${top}px, 0)` }} />
    </div>
  );
}

export function Cursor() {
  const [prefs] = usePrefs();
  const dot = useRef<HTMLDivElement>(null);
  const ring = useRef<HTMLDivElement>(null);
  const enabled = prefs.cursor && prefs.motion && !reducedSystem();

  useEffect(() => {
    if (!enabled || !finePointer()) return;
    document.documentElement.classList.add("has-cursor");
    let x = -100, y = -100, rx = x, ry = y, frame = 0, running = false;
    const loop = () => {
      rx += (x - rx) * 0.2; ry += (y - ry) * 0.2;
      if (dot.current) dot.current.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      if (ring.current) ring.current.style.transform = `translate3d(${rx}px, ${ry}px, 0)`;
      if (Math.abs(x - rx) + Math.abs(y - ry) > 0.3) frame = requestAnimationFrame(loop);
      else running = false;
    };
    const kick = () => { if (!running) { running = true; frame = requestAnimationFrame(loop); } };
    const move = (e: PointerEvent) => {
      x = e.clientX; y = e.clientY;
      const target = e.target as Element | null;
      const text = !!target?.closest("input:not([type='range']), textarea");
      const hot = !!target?.closest("a, button, [role='button'], select, input[type='range'], .pilot, .cell");
      ring.current?.classList.toggle("hot", hot && !text);
      ring.current?.classList.toggle("text", text);
      dot.current?.classList.add("on");
      ring.current?.classList.add("on");
      kick();
    };
    const leave = () => { dot.current?.classList.remove("on"); ring.current?.classList.remove("on"); };
    const down = () => ring.current?.classList.add("press");
    const up = () => ring.current?.classList.remove("press");
    window.addEventListener("pointermove", move, { passive: true });
    document.documentElement.addEventListener("pointerleave", leave);
    window.addEventListener("pointerdown", down);
    window.addEventListener("pointerup", up);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", move);
      document.documentElement.removeEventListener("pointerleave", leave);
      window.removeEventListener("pointerdown", down);
      window.removeEventListener("pointerup", up);
      document.documentElement.classList.remove("has-cursor");
    };
  }, [enabled]);

  if (!enabled) return null;
  return (
    <>
      <div ref={ring} className="cursor-ring" aria-hidden="true"><span /></div>
      <div ref={dot} className="cursor-dot" aria-hidden="true" />
    </>
  );
}
