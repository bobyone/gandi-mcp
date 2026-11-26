<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Glossary

One concept, one term, used everywhere (UI, messages, documentation, code,
API). Add a term here before using it. The "UI label" column gives the English
label of a term displayed in the MCP App and its catalog key; its label in each
language is in the table below, generated from the UI catalogs. A term not shown
in the UI says "not displayed".

| Term | Definition | Code identifier | UI label |
| --- | --- | --- | --- |
| Gandi | The registrar and hosting provider whose public API v5 this project uses. | `gandi` | Gandi (never translated) |
| Gandi API | The Gandi public HTTP API, version 5. | `gandi_api` | not displayed |
| Sandbox | The Gandi test environment, where operations have no real effect nor cost; it has its own accounts and tokens. | `sandbox` | Sandbox (`environment.sandbox`) |
| Personal mode | The local MCP server running on the user's computer over `stdio`. | `personal_mode` | not displayed |
| MCP App | The UI provided by the server and rendered by the MCP client. | `mcp_app` | not displayed |
| Tool | An operation exposed by the server to the MCP client. | `tool` | not displayed |
| Account | A Gandi identity configured in the personal mode: a name chosen by the user and a Personal Access Token. | `account` | not displayed |
| Default account | The account used when a tool call names no account. | `default_account` | Default account (`status.default`) |
| Personal Access Token (PAT) | A Gandi secret granting API rights to an account; stored in the OS keyring only. | `personal_access_token` | Personal Access Token (`field.token`; never translated) |
| Confirmation | The user's explicit agreement, requested by the server, before a destructive or billable operation. | `confirmation` | not displayed |
| Destructive operation | An operation that deletes or irreversibly changes a Gandi resource. | `destructive` | not displayed |
| Billable operation | An operation that charges the Gandi account (purchase, renewal, transfer). | `billable` | not displayed |
| Environment | The Gandi target of an account: production or sandbox. | `environment` | Environment (`field.environment`) |
| Production | The real Gandi environment, where operations have effects and costs. | `production` | Production (`environment.production`) |
| Read-only account | An account whose write operations are all refused. | `read_only` | Read-only account (`field.readOnly`) |
| Secret store | The operating system keyring, the only place where a Personal Access Token is kept. | `secret_store` | not displayed |
| Preferences | Local settings without any secret: the accounts and the default account. | `preferences` | not displayed |
| Token entry session | A local page to enter a Personal Access Token without the MCP App. | `token_entry_session` | not displayed |
| Operation | A call to Gandi on behalf of an account. | `operation` | not displayed |
| Read operation | An operation that only reads Gandi resources. | `read_operation` | not displayed |
| Write operation | An operation that changes Gandi resources; destructive and billable operations are write operations. | `write_operation` | not displayed |
| Confirmation channel | A way to ask for a confirmation: elicitation or local page. | `confirmation_channel` | not displayed |
| Local page | A temporary page served by the personal mode on `127.0.0.1`, protected by a single-use code, shown to the user through URL elicitation or the browser and never given to the model. | `local_page` | not displayed |
| Pending removal | An account whose removal started and did not finish (failure, cancellation, crash); it can only be removed again, which completes the removal. | `removal_pending` | Removal not finished (`status.removalPending`) |
| Pending confirmation | A confirmation waiting for the user's answer on a local page; its identifier, given back by the model, is valid once and for the same operation only. | `pending_confirmation` | not displayed |
| Untrusted data | Content coming from tool results or free inputs, which may contain prompt injection. | `untrusted` | not displayed |
| Domain | A domain name managed by a Gandi account. | `domain` | not displayed yet |
| TLD | The ending of a domain name (`.fr`, `.com`), with its rules: durations and allowed procedures. | `tld` | not displayed yet |
| Domain contact | A person or structure in one of the roles of a domain: owner, admin contact, tech contact or billing contact; personal data. | `contact` | not displayed yet |
| Owner | The domain contact holding the domain. | `owner` | not displayed yet |
| Admin contact | The domain contact handling the administration of the domain. | `admin` | not displayed yet |
| Tech contact | The domain contact handling the technical matters of the domain. | `tech` | not displayed yet |
| Billing contact | The domain contact receiving the invoices of the domain. | `bill` | not displayed yet |
| Quote | The availability and price announced by Gandi for a billable procedure on a name. | `quote` | not displayed yet |
| Order | A billable procedure confirmed by the user, with its account, paying organization, name, duration and accepted price. | `order` | not displayed yet |
| Paying organization | The Gandi organization charged for an order; a default one is stored in the account preferences. | `paying_organization` | not displayed yet |
| Asynchronous operation | A procedure Gandi runs later (registration, owner change, transfer), followed by its step and state. | `async_operation` | not displayed |
| Dry run | A simulation of a procedure by Gandi, without effect nor charge. | `dry_run` | not displayed |
| Nameserver | A DNS server declared for a domain. | `nameserver` | not displayed yet |
| Glue record | The IP addresses of a nameserver named inside the domain itself. | `glue_record` | not displayed |
| DNSSEC key | A public key published at the registry to sign the zone of a domain. | `dnssec_key` | not displayed |
| Web redirection | A redirection of a host of a domain to a URL, served by Gandi. | `web_redirection` | not displayed |
| Tag | A label attached to a domain to organize domains. | `tag` | not displayed yet |
| Transfer lock | The status forbidding the transfer of a domain to another registrar. | `transfer_lock` | not displayed yet |
| Authorization code | The secret code required to transfer a domain between registrars. | `authinfo` | not displayed |
| Transfer in | Moving a domain from another registrar to Gandi; a billable procedure. | `transfer_in` | not displayed |
| Transfer out | Moving a domain from Gandi to another registrar. | `transfer_out` | not displayed |
| Owner change | Changing the owner of a domain; may be billable. | `owner_change` | not displayed |
| Trademark claim | The trademark notice to accept before registering some names. | `claim` | not displayed |
| Automatic renewal | The renewal Gandi performs by itself before expiry. | `autorenew` | not displayed yet |
| Renewal | Extending the registration of a domain; a billable procedure. | `renewal` | not displayed yet |
| Restore | Recovering an expired domain during its redemption period; a billable procedure. | `restore` | not displayed |

## UI labels by language

Generated from `ui/src/i18n/locales/`; to be reviewed by native speakers like
the catalogs.

<!-- ui-labels:start (generated by scripts/check_ui_translations.py) -->

| Language | Environment | Production | Sandbox | Read-only account | Default account | Personal Access Token | Pending removal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `az` | Mühit | İstehsal | Sandbox | Yalnız oxumaq üçün hesab | Defolt hesab | Personal Access Token | Silinmə yarımçıqdır |
| `be` | Асяроддзе | Рабочае | Sandbox | Уліковы запіс толькі для чытання | Уліковы запіс па змаўчанні | Personal Access Token | Выдаленне не завершана |
| `bg` | Среда | Производствена | Sandbox | Акаунт само за четене | Акаунт по подразбиране | Personal Access Token | Премахването не е завършено |
| `bs` | Okruženje | Produkcija | Sandbox | Račun samo za čitanje | Zadani račun | Personal Access Token | Uklanjanje nije završeno |
| `ca` | Entorn | Producció | Sandbox | Compte de només lectura | Compte predeterminat | Personal Access Token | Supressió pendent |
| `cnr` | Okruženje | Produkcija | Sandbox | Nalog samo za čitanje | Podrazumijevani nalog | Personal Access Token | Uklanjanje nije završeno |
| `cs` | Prostředí | Produkce | Sandbox | Účet jen pro čtení | Výchozí účet | Personal Access Token | Odebrání nedokončeno |
| `da` | Miljø | Produktion | Sandbox | Skrivebeskyttet konto | Standardkonto | Personal Access Token | Fjernelse ikke fuldført |
| `de` | Umgebung | Produktion | Sandbox | Schreibgeschütztes Konto | Standardkonto | Personal Access Token | Entfernen nicht abgeschlossen |
| `el` | Περιβάλλον | Παραγωγή | Sandbox | Λογαριασμός μόνο για ανάγνωση | Προεπιλεγμένος λογαριασμός | Personal Access Token | Εκκρεμεί αφαίρεση |
| `en` | Environment | Production | Sandbox | Read-only account | Default account | Personal Access Token | Removal not finished |
| `es` | Entorno | Producción | Sandbox | Cuenta de solo lectura | Cuenta predeterminada | Personal Access Token | Eliminación pendiente |
| `et` | Keskkond | Tootmine | Sandbox | Kirjutuskaitstud konto | Vaikekonto | Personal Access Token | Eemaldamine pooleli |
| `fi` | Ympäristö | Tuotanto | Sandbox | Vain luku -tili | Oletustili | Personal Access Token | Poisto kesken |
| `fr` | Environnement | Production | Sandbox | Compte en lecture seule | Compte par défaut | Personal Access Token | Suppression inachevée |
| `ga` | Timpeallacht | Táirgeacht | Sandbox | Cuntas inléite amháin | Cuntas réamhshocraithe | Personal Access Token | Bainteoireacht gan chríochnú |
| `hr` | Okruženje | Produkcija | Sandbox | Račun samo za čitanje | Zadani račun | Personal Access Token | Uklanjanje nije dovršeno |
| `hu` | Környezet | Éles | Sandbox | Csak olvasható fiók | Alapértelmezett fiók | Personal Access Token | Befejezetlen eltávolítás |
| `hy` | Միջավայր | Աշխատանքային | Sandbox | Միայն կարդալու հաշիվ | Լռելյայն հաշիվ | Personal Access Token | Հեռացումն անավարտ է |
| `is` | Umhverfi | Framleiðsla | Sandbox | Skrifvarinn reikningur | Sjálfgefinn reikningur | Personal Access Token | Fjarlæging ólokið |
| `it` | Ambiente | Produzione | Sandbox | Account in sola lettura | Account predefinito | Personal Access Token | Rimozione da completare |
| `ka` | გარემო | სამუშაო | Sandbox | მხოლოდ წაკითხვის ანგარიში | ნაგულისხმევი ანგარიში | Personal Access Token | წაშლა დაუსრულებელია |
| `lb` | Ëmfeld | Produktioun | Sandbox | Nëmme liesbare Kont | Standardkont | Personal Access Token | Ewechhuelen net ofgeschloss |
| `lt` | Aplinka | Gamybinė | Sandbox | Tik skaitoma paskyra | Numatytoji paskyra | Personal Access Token | Šalinimas nebaigtas |
| `lv` | Vide | Ražošanas | Sandbox | Tikai lasāms konts | Noklusējuma konts | Personal Access Token | Noņemšana nav pabeigta |
| `mk` | Околина | Продукциска | Sandbox | Сметка само за читање | Стандардна сметка | Personal Access Token | Отстранувањето не е завршено |
| `mt` | Ambjent | Produzzjoni | Sandbox | Kont għall-qari biss | Kont awtomatiku | Personal Access Token | Tneħħija mhux lesta |
| `nb` | Miljø | Produksjon | Sandbox | Skrivebeskyttet konto | Standardkonto | Personal Access Token | Fjerning ikke fullført |
| `nl` | Omgeving | Productie | Sandbox | Alleen-lezenaccount | Standaardaccount | Personal Access Token | Verwijdering onvoltooid |
| `nn` | Miljø | Produksjon | Sandbox | Skriveverna konto | Standardkonto | Personal Access Token | Fjerning ikkje fullført |
| `pl` | Środowisko | Produkcja | Sandbox | Konto tylko do odczytu | Konto domyślne | Personal Access Token | Usuwanie niedokończone |
| `pt` | Ambiente | Produção | Sandbox | Conta só de leitura | Conta predefinida | Personal Access Token | Remoção por concluir |
| `rm` | Ambient | Producziun | Sandbox | Conto mo per leger | Conto da standard | Personal Access Token | Allontanament betg terminà |
| `ro` | Mediu | Producție | Sandbox | Cont doar pentru citire | Cont implicit | Personal Access Token | Eliminare neterminată |
| `ru` | Среда | Рабочая | Sandbox | Учётная запись только для чтения | Учётная запись по умолчанию | Personal Access Token | Удаление не завершено |
| `sk` | Prostredie | Produkcia | Sandbox | Účet len na čítanie | Predvolený účet | Personal Access Token | Odstránenie nedokončené |
| `sl` | Okolje | Produkcija | Sandbox | Račun samo za branje | Privzeti račun | Personal Access Token | Odstranitev ni dokončana |
| `sq` | Mjedisi | Prodhim | Sandbox | Llogari vetëm për lexim | Llogaria parazgjedhje | Personal Access Token | Heqje e papërfunduar |
| `sr-Cyrl` | Окружење | Продукција | Sandbox | Налог само за читање | Подразумевани налог | Personal Access Token | Уклањање није завршено |
| `sr-Latn` | Okruženje | Produkcija | Sandbox | Nalog samo za čitanje | Podrazumevani nalog | Personal Access Token | Uklanjanje nije završeno |
| `sv` | Miljö | Produktion | Sandbox | Skrivskyddat konto | Standardkonto | Personal Access Token | Borttagning ej slutförd |
| `tr` | Ortam | Üretim | Sandbox | Salt okunur hesap | Varsayılan hesap | Personal Access Token | Kaldırma tamamlanmadı |
| `uk` | Середовище | Робоче | Sandbox | Обліковий запис лише для читання | Обліковий запис за замовчуванням | Personal Access Token | Видалення не завершено |

<!-- ui-labels:end -->
