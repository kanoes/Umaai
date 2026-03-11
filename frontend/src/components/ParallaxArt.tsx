import { useState } from "react";
import type { CSSProperties } from "react";

import type { CharacterImage, Theme } from "../types/api";
import { hexToRgba } from "../utils/color";

type ParallaxArtProps = {
  image: CharacterImage;
  name: string;
  theme: Theme;
  compact?: boolean;
};

export function ParallaxArt({ image, name, theme, compact = false }: ParallaxArtProps) {
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const style = {
    "--art-main": theme.image_main,
    "--art-sub": theme.image_sub,
    "--art-border": hexToRgba(theme.border, 0.35),
    transform: `perspective(1000px) rotateX(${offset.y * -3}deg) rotateY(${offset.x * 4}deg)`,
  } as CSSProperties;

  return (
    <div
      className={`parallax-art ${compact ? "compact" : ""}`.trim()}
      style={style}
      onMouseMove={(event) => {
        const rect = event.currentTarget.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        setOffset({ x, y });
      }}
      onMouseLeave={() => setOffset({ x: 0, y: 0 })}
    >
      <div className="parallax-art__orb parallax-art__orb--back" />
      <div className="parallax-art__orb parallax-art__orb--front" />
      {image.ready && image.path ? (
        <img className="parallax-art__image" src={`/${encodeURI(image.path)}`} alt={name} loading="lazy" />
      ) : (
        <div className="parallax-art__placeholder">No Art</div>
      )}
      <div className="parallax-art__shine" />
    </div>
  );
}
