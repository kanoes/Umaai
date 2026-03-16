import type { CSSProperties } from "react";
import { Link } from "react-router-dom";

import type { CharacterSummary } from "../types/api";
import { hexToRgba } from "../utils/color";
import { characterName, metricValue } from "../utils/format";
import { ParallaxArt } from "./ParallaxArt";

type CharacterCardProps = {
  character: CharacterSummary;
  mode?: "grid" | "compact";
};

const DISTANCE_LABELS: Record<string, string> = {
  short: "短距",
  mile: "英里",
  middle: "中距",
  long: "长距",
};

const STYLE_LABELS: Record<string, string> = {
  runner: "逃",
  leader: "先",
  betweener: "差",
  chaser: "追",
};

export function CharacterCard({ character, mode = "grid" }: CharacterCardProps) {
  const style = {
    "--card-main": character.theme.main,
    "--card-sub": character.theme.sub,
    "--card-outline": hexToRgba(character.theme.border, 0.26),
  } as CSSProperties;
  const distanceTag = character.filters.distance_tags[0];
  const styleTag = character.filters.style_tags[0];
  const snippet = character.persona_line?.split("·").at(-1)?.trim() || character.tagline || "点进去看看这位。";
  const personaTag = character.personality_tags[0];

  return (
    <Link className={`character-card ${mode}`.trim()} to={`/characters/${character.slug}`} style={style}>
      <div className="character-card__media">
        <ParallaxArt compact={mode === "compact"} image={character.image} name={characterName(character)} theme={character.theme} />
      </div>
      <div className="character-card__body">
        <div className="character-card__topline">
          <span className="character-card__stamp">{character.theme_group}</span>
          <span className="character-card__spark">{personaTag || "已收录"}</span>
        </div>
        <div className="character-card__nameplate">
          <span className="character-card__name">{characterName(character)}</span>
          <span className="character-card__name-sub">{character.name_ja || character.name_en}</span>
        </div>
        <p className="character-card__tagline">{snippet}</p>
        <div className="character-card__chips">
          {distanceTag ? <span>{DISTANCE_LABELS[distanceTag] || distanceTag}</span> : null}
          {styleTag ? <span>{STYLE_LABELS[styleTag] || styleTag}</span> : null}
          <span>衣装 {character.counts.character_cards}</span>
          <span>支援 {character.counts.support_cards}</span>
          <span>身高 {metricValue(character.metrics?.height_cm, "cm")}</span>
        </div>
        <div className="character-card__footer">
          <small>{character.persona_line || character.name_ja || character.name_en}</small>
          <strong>详情</strong>
        </div>
      </div>
    </Link>
  );
}
