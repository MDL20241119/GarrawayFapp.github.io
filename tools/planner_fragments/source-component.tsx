import { withBasePath } from "./base-path";
import "./ramen-special.css";

export default function RamenSpecial() {
  return (
    <section id="gf-ramen-special" aria-labelledby="gf-special-title">
      <div>
        <p className="gf-special-kicker">GARRAWAY F / SPECIAL SITE / 2026.10.07–11</p>
        <h2 id="gf-special-title">RAMEN TECH 特設サイト</h2>
        <p className="gf-special-text">Garraway Fのミートアップから、街じゅうのイベントへ。<br />気になる予定を選んで、会場間の移動も含めた一日をつくろう。</p>
      </div>
      <div className="gf-special-side">
        <figure><img src={withBasePath("/ramen-tech-2026/assets/tonkotsu.svg")} width="110" height="105" alt="とんこつラーメンの非公式キャラ" /><figcaption>非公式キャラ</figcaption></figure>
        <div className="gf-special-links">
          <a href={withBasePath("/ramen-tech-2026/")}>特設サイトを開く ↗</a>
          <a href={withBasePath("/ramen-tech-2026/") + "?venue=garraway&date=any#garraway-featured"}>Garraway Fのイベントを見る ↗</a>
        </div>
      </div>
    </section>
  );
}
