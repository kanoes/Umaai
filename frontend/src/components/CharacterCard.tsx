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

export function CharacterCard({ character, mode = "grid" }: CharacterCardProps) {
  const style = {
    "--card-main": character.theme.main,
    "--card-sub": character.theme.sub,
    "--card-outline": hexToRgba(character.theme.border, 0.26),
  } as CSSProperties;

  return (
    <Link className={`character-card ${mode}`.trim()} to={`/characters/${character.slug}`} style={style}>
      <div className="character-card__media">
        <ParallaxArt compact={mode === "compact"} image={character.image} name={characterName(character)} theme={character.theme} />
      </div>
      <div className="character-card__body">
        <div className="character-card__nameplate">
          <span className="character-card__name">{characterName(character)}</span>
          <span className="character-card__name-sub">{character.name_ja || character.name_en}</span>
        </div>
        <p className="character-card__tagline">{character.tagline || "角色资料已收录，等待你继续深入。"} </p>
        <div className="character-card__chips">
          <span>衣装 {character.counts.character_cards}</span>
          <span>支援卡 {character.counts.support_cards}</span>
          <span>关系 {character.counts.relations}</span>
          <span>身高 {metricValue(character.metrics?.height_cm, "cm")}</span>
        </div>
      </div>
    </Link>
  );
}
