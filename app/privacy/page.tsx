import type { Metadata } from "next";
import Link from "next/link";
import { CONTACT_EMAILS, SITE_LINKS } from "../site-links";
import { SubpageFooter, SubpageHeader } from "../subpage-chrome";

export const metadata: Metadata = {
  title: "プライバシーポリシー｜Garraway F",
  description: "Garraway F公式ウェブサイトにおける個人情報、Cookieおよび外部送信の取扱いをご案内します。",
};

const externalTransmissions = [
  {
    service: "GitHub Pages",
    operator: "GitHub, Inc.",
    data: "IPアドレス、端末・ブラウザ情報、アクセス日時、閲覧ページ、参照元URL等",
    purpose: "本サイトの配信、安定運用、不正アクセスの検知およびセキュリティ確保",
    policy: "https://docs.github.com/ja/site-policy/privacy-policies/github-general-privacy-statement",
  },
  {
    service: "Google Fonts",
    operator: "Google LLC",
    data: "IPアドレス、端末・ブラウザ情報、アクセス日時、参照元URL等",
    purpose: "本サイトで使用する書体の配信、サービスの提供・改善",
    policy: "https://policies.google.com/privacy?hl=ja",
  },
  {
    service: "Google マップ",
    operator: "Google LLC",
    data: "IPアドレス、端末・ブラウザ情報、Cookieその他の識別子、閲覧・操作情報等",
    purpose: "所在地、地図および経路情報の表示、サービスの提供・改善",
    policy: "https://policies.google.com/privacy?hl=ja",
  },
  {
    service: "Facebookページプラグイン",
    operator: "Meta Platforms, Inc.",
    data: "IPアドレス、端末・ブラウザ情報、Cookieその他の識別子、閲覧・操作情報等",
    purpose: "Garraway FのFacebookページおよびイベント情報の表示、サービスの提供・改善",
    policy: "https://www.facebook.com/privacy/policy/",
  },
] as const;

export default function PrivacyPage() {
  return (
    <main id="top" className="subpage privacyPage">
      <SubpageHeader />

      <section className="subpageHero privacyPageHero">
        <div>
          <p><span /> PRIVACY &amp; DATA</p>
          <h1>大切な情報を、<br /><em>誠実に扱う。</em></h1>
        </div>
        <aside>
          <strong>POLICY</strong>
          <p>Garraway F公式ウェブサイトにおける、個人情報・Cookie・外部送信の取扱いを定めます。</p>
          <a href="#policy">本文を確認する ↓</a>
        </aside>
      </section>

      <article className="privacyDocument" id="policy">
        <header className="privacyDocumentHead">
          <p>制定日：2026年9月2日</p>
          <h2>プライバシーポリシー</h2>
          <p>
            株式会社Serendipity（以下「当社」といいます。）は、Garraway F公式ウェブサイト
            （以下「本サイト」といいます。）の運営に伴う個人情報その他の利用者情報を、以下のとおり取り扱います。
          </p>
          <div className="privacyScopeNote">
            <strong>対象範囲</strong>
            <p>本ポリシーは本サイトに適用されます。会員登録、チェックイン、ポイント、注文・決済等を行うGarraway F Webアプリには、別途定める利用規約・プライバシーポリシーが適用されます。</p>
            <a href={SITE_LINKS.webAppTerms} target="_blank" rel="noreferrer">Webアプリ利用規約・プライバシーポリシー ↗</a>
          </div>
        </header>

        <section>
          <span className="privacySectionNo">01</span>
          <div>
            <h2>取得する情報</h2>
            <p>当社または本サイトで利用する外部サービスの提供者は、次の情報を取得することがあります。</p>
            <ul>
              <li><b>お問い合わせ情報</b>：相談種別、氏名、会社・団体名、メールアドレス、電話番号、お問い合わせ内容</li>
              <li><b>通信・閲覧情報</b>：IPアドレス、端末・ブラウザ情報、アクセス日時、閲覧ページ、参照元URL、Cookieその他の識別子</li>
              <li><b>連絡履歴</b>：当社からの回答、打合せ、イベント・視察・共創相談等に関する連絡内容</li>
            </ul>
            <p className="privacyCallout">お問い合わせフォームへの入力内容は本サイトのサーバーには保存されません。送信時に利用者のメールアプリが起動し、利用者が送信操作を行った時点で、メールとして公式窓口へ送信されます。</p>
          </div>
        </section>

        <section>
          <span className="privacySectionNo">02</span>
          <div>
            <h2>利用目的</h2>
            <ol>
              <li>お問い合わせへの回答、本人確認および必要な連絡</li>
              <li>共創、イベント開催、取材、視察その他の相談内容の検討・調整・実施</li>
              <li>本サイトおよびGarraway Fの運営、品質改善、利用状況の分析</li>
              <li>不正利用の防止、セキュリティの確保およびトラブル対応</li>
              <li>法令、契約およびGarraway Fの利用ルールへの対応</li>
            </ol>
            <p>メールマガジン、広告その他の継続的な案内に利用する場合は、あらかじめ別途同意を取得します。</p>
          </div>
        </section>

        <section>
          <span className="privacySectionNo">03</span>
          <div>
            <h2>第三者提供</h2>
            <p>当社は、次の場合を除き、本人の同意なく個人データを第三者に提供しません。</p>
            <ul>
              <li>法令に基づく場合</li>
              <li>人の生命、身体または財産の保護のために必要で、本人の同意を得ることが困難な場合</li>
              <li>公衆衛生の向上または児童の健全な育成のために特に必要で、本人の同意を得ることが困難な場合</li>
              <li>国または地方公共団体等の法令上の事務に協力する必要があり、同意取得がその遂行を妨げるおそれがある場合</li>
            </ul>
            <p>イベント主催者・共催者その他の関係者へ情報提供が必要な場合は、提供先、提供項目および利用目的を示し、法令上必要な同意を個別に取得します。</p>
          </div>
        </section>

        <section>
          <span className="privacySectionNo">04</span>
          <div>
            <h2>取扱いの委託</h2>
            <p>当社は、メール、ウェブサイト運用その他の業務の全部または一部を外部事業者へ委託することがあります。この場合、委託先を適切に選定し、契約その他の方法により必要かつ適切な監督を行います。</p>
          </div>
        </section>

        <section>
          <span className="privacySectionNo">05</span>
          <div>
            <h2>Cookie・外部送信</h2>
            <p>本サイトは、現時点で広告配信または独自のアクセス解析を目的とするCookieを使用していません。一方、サイト配信および埋め込みコンテンツの表示に伴い、利用者の端末から次の事業者へ情報が送信されることがあります。</p>
            <div className="privacyTableWrap">
              <table>
                <thead>
                  <tr><th>サービス・送信先</th><th>送信される情報</th><th>利用目的</th></tr>
                </thead>
                <tbody>
                  {externalTransmissions.map((item) => (
                    <tr key={item.service}>
                      <th>{item.service}<small>{item.operator}</small><a href={item.policy} target="_blank" rel="noreferrer">各社のプライバシーポリシー ↗</a></th>
                      <td>{item.data}</td>
                      <td>{item.purpose}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p>各社は、送信された情報を各社の規程に基づき国外で取り扱う場合があります。Cookieはブラウザの設定で無効化できますが、地図やFacebook情報等の一部が正しく表示されないことがあります。外部サイトへ移動した後の情報取扱いには、移動先の規約・プライバシーポリシーが適用されます。</p>
          </div>
        </section>

        <section>
          <span className="privacySectionNo">06</span>
          <div>
            <h2>安全管理措置</h2>
            <p>当社は、個人データを適切に管理するため、取扱担当者と権限の限定、アカウント・認証情報の管理、不正アクセス等の防止、取扱状況の確認、従業者への周知および委託先の監督等、必要かつ適切な安全管理措置を講じます。</p>
          </div>
        </section>

        <section>
          <span className="privacySectionNo">07</span>
          <div>
            <h2>保存期間</h2>
            <p>お問い合わせ情報および対応履歴は、対応に必要な期間のみ利用し、対応完了後、当社が管理するメールボックス等から速やかに削除します（原則30日以内）。ただし、申込み・契約等に移行した場合、法令上の保存義務がある場合、または紛争対応に必要な場合は、その必要期間に限り保存します。通信・閲覧情報は、各サービス提供者が定める期間保存されます。</p>
          </div>
        </section>

        <section>
          <span className="privacySectionNo">08</span>
          <div>
            <h2>開示等の請求</h2>
            <p>本人は、当社が保有する本人に関する保有個人データについて、利用目的の通知、開示、訂正・追加・削除、利用停止・消去、第三者提供の停止および第三者提供記録の開示を請求できます。</p>
            <p>請求を希望する場合は、下記窓口へご連絡ください。本人または代理人であることを確認したうえで、法令に従い、原則として手数料なしで対応します。確認方法と必要事項は、請求内容に応じて個別にご案内します。</p>
          </div>
        </section>

        <section>
          <span className="privacySectionNo">09</span>
          <div>
            <h2>未成年者の情報</h2>
            <p>未成年者が本サイトから個人情報を送信する場合は、必要に応じて法定代理人の同意を得てください。</p>
          </div>
        </section>

        <section>
          <span className="privacySectionNo">10</span>
          <div>
            <h2>本ポリシーの変更</h2>
            <p>当社は、法令または本サイトの内容等の変更に応じて本ポリシーを改定することがあります。重要な変更を行う場合は、本サイト上で変更内容と効力発生日を分かりやすく周知し、法令上必要な場合は本人の同意を取得します。</p>
          </div>
        </section>

        <section className="privacyContactSection">
          <span className="privacySectionNo">11</span>
          <div>
            <h2>事業者情報・お問い合わせ窓口</h2>
            <dl>
              <div><dt>事業者名</dt><dd>株式会社Serendipity</dd></div>
              <div><dt>所在地</dt><dd>福岡県福岡市東区美和台3丁目19番8号</dd></div>
              <div><dt>代表者</dt><dd>代表取締役　佐藤 加奈</dd></div>
              <div>
                <dt>窓口</dt>
                <dd>
                  {CONTACT_EMAILS.map((email) => <a href={`mailto:${email}`} key={email}>{email}</a>)}
                </dd>
              </div>
            </dl>
          </div>
        </section>

        <nav className="privacyEndLinks" aria-label="関連する方針と窓口">
          <Link href="/contact">お問い合わせへ進む →</Link>
          <a href={SITE_LINKS.webAppTerms} target="_blank" rel="noreferrer">Webアプリ規約を確認する ↗</a>
        </nav>
      </article>

      <SubpageFooter />
    </main>
  );
}
