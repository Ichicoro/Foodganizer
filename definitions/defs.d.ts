interface Window {
  $$: (selector: string) => Element
  $$all: (selector: string) => Element[]
  $$onReady: (func: () => void) => void
}

declare var window: Window & typeof globalThis