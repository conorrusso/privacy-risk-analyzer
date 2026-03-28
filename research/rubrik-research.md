# Bandit Rubric Research

## Search 1 — Regulatory Baseline
[GDPR Art. 28 — DPA Completeness (D8)
This is your structural backbone. Art. 28(3) requires a binding contract that sets out the subject-matter and duration of processing, the nature and purpose, the type of personal data, categories of data subjects, and the obligations and rights of the controller. GDPR Info The contract must stipulate eight mandatory provisions:
The Art. 28(3)(a)–(h) checklist — a DPA missing any of these is non-compliant:

(a) Documented instructions — The processor may only process personal data on documented instructions from the controller, including with regard to transfers to third countries, unless required by law. GDPR-Text
(b) Confidentiality — Persons authorized to process data must have committed to confidentiality, including employees and temporary workers, and the confidentiality agreement must be sufficiently broad to cover all personal data processed on behalf of the controller. Byte Back
(c) Security measures — Per Art. 32 requirements.
(d) Sub-processing — The processor shall not engage another processor without prior specific or general written authorization of the controller. In the case of general written authorization, the processor shall inform the controller of any intended changes concerning the addition or replacement of other processors, giving the controller the opportunity to object. GDPR Info
(e) Data subject rights assistance — The contract must provide for the processor to take appropriate technical and organizational measures to help the controller respond to requests from individuals exercising their rights. ICO
(f) Assistance with Arts. 32–36 obligations — The processor must assist the controller in ensuring compliance with obligations regarding security of processing, breach notification, and data protection impact assessments. Data Protection Commission
(g) Deletion/return — The processor agrees to delete all personal data upon the termination of services or return the data to the controller. GDPR
(h) Audit rights — The processor must allow the controller to conduct an audit and will provide whatever information necessary to prove compliance. GDPR

Critical enforcement note: The EDPB Guidelines 7/2020 reinforce that failure to enter into a written contract is itself an infringement of the GDPR, and both the controller and processor are responsible for ensuring a contract exists. Byte Back
Scoring implication for D8: A vendor DPA that omits even one of these eight provisions is structurally deficient. Boilerplate language that doesn't address the specific processing context is also a red flag — the EDPB requires entities to conduct a thorough analysis and not simply use boilerplate DPAs. Byte Back

D1 — Data Minimization
GDPR Art. 5(1)(c): Personal data must be "adequate, relevant and limited to what is necessary in relation to the purposes for which they are processed."
The CJEU has held that data minimization gives expression to the principle of proportionality, meaning that interference with the fundamental right to data protection must be proportionate. Unlike the previous Directive, which required data not be "excessive," the GDPR specifies it must be "limited to what is necessary." GDPRhub
The CJEU ruled in Schrems v Meta (Case C-446/21, Oct 2024) that storing personal data of social network users for an unlimited period for targeted advertising constitutes a disproportionate interference, and that indiscriminate use of all personal data held by a platform for advertising, irrespective of sensitivity, does not appear proportionate. GDPRhub
CCPA/CPRA: The California Privacy Protection Agency released its first enforcement advisory in April 2024, calling data minimization a "foundational principle" of the CCPA. GDPRLocal Service providers must restrict data usage to the specific purposes enumerated in the contract.
Enforcement examples:

In December 2023, France's CNIL fined Amazon France Logistique €32 million for excessively intrusive employee monitoring. Warehouse employees were tracked via scanners recording productivity, idle time, and task speed. The CNIL found this disproportionate, and data was retained longer than necessary. These practices violated data minimization, lawful processing, and transparency provisions. CookieYes
German retailer notebooksbilliger.de received a €10.4 million fine for employee monitoring via CCTV in break rooms and warehouses, overstepping legitimate interest and violating data minimization by keeping footage over 60 days. Transcend

Red flags in vendor policies: Vague language like "we may collect data as needed to provide services" without specifying categories, or open-ended purposes like "improving our products and services" without limits.

D2 — Sub-processor Management
GDPR Art. 28(2) and (4): The same data protection obligations set out in the controller-processor contract shall be imposed on any sub-processor by way of a contract. Where that sub-processor fails to fulfill its obligations, the initial processor remains fully liable to the controller. GDPR Info
CCPA/CPRA: Processors must notify the business if they are involving another person or party in the data processing and ensure that relationship is bound by the same contractual obligations. Transcend
Key conflict between frameworks: Under GDPR, the processor choice is "prior specific or general written authorization." Under CPRA, the obligation is notification-based with the same level of contractual flow-down. The GDPR mechanism is more prescriptive — it requires the right to object, not merely be notified.
Red flags: No published sub-processor list, no mechanism for notification of changes, no specified objection period, or DPA language that allows sub-processor changes with only "reasonable efforts" to notify.

D3 — Data Subject Rights
GDPR Chapter III (Arts. 12–23): Rights include access (Art. 15), rectification (Art. 16), erasure (Art. 17), restriction (Art. 18), data portability (Art. 20), and objection (Art. 21). The processor's obligation under Art. 28(3)(e) is to assist the controller in fulfilling these.
CCPA/CPRA: Service providers are not required to respond to privacy requests submitted directly to them, but they are required to cooperate with a business attempting to fulfill a consumer request — providing personal data collected, responding to information requests, and deleting or correcting information upon request. Transcend
The CPRA expanded rights to include correction (new) and limiting use of sensitive personal information.
Enforcement: The Irish DPC fined Meta €390 million in January 2023 for practices that breached Art. 5(1)(a), holding that Meta's Terms of Use did not clearly disclose data processing activities, purposes, or legal basis. Secureframe
TikTok was fined €345 million in September 2023 for GDPR violations concerning children's data, including issues with default settings making child accounts public and inadequate age verification. The decision cited violations of fairness, data minimization, and privacy by design. CookieYes

D4 — Cross-Border Transfer Mechanisms
GDPR Chapter V (Arts. 44–50): Article 44 introduces the overarching principle: any data transfer must not undermine the level of protection guaranteed by the GDPR. Article 45 allows transfers to jurisdictions deemed "adequate." Article 46 applies when adequacy is not established, requiring appropriate safeguards such as SCCs or BCRs. Cybersecurityattorney
Post-Schrems II reality: The CJEU stressed the possible need for supplementary measures in addition to appropriate safeguards when transferring data outside the EEA. Data exporters are responsible for verifying, on a case-by-case basis, whether the law or practice of the recipient country impinges on the effectiveness of the safeguards. EDPB
The €1.2B enforcement precedent: In May 2023, the Irish DPC held that Meta infringed Art. 46(1) by continuing to transfer data to the US following Schrems II, even though Meta used the 2021 SCCs and supplementary measures. The DPC found these arrangements did not address the risks identified by the CJEU. California Lawyers Association
Current state — EU-US Data Privacy Framework: Since July 10, 2023, there has been an adequacy decision for the EU-US Data Privacy Framework, allowing transfers to DPF-certified US organizations. GDPR Info However, legal challenges are anticipated (termed "Schrems III") that could place the framework under judicial review, so many organizations continue to maintain SCCs and TIAs as fallback mechanisms. Cybersecurityattorney
New SCCs (June 2021): The requirements of Art. 28 have been incorporated into Module 2 (C2P) and Module 3 (P2P), so controllers and processors using these modules do not need a separate DPA. The new SCCs now require a "transfer impact assessment" documenting the specific circumstances of the transfer and the laws in the destination country. European Commission
Red flags: Vendor claims "data stays in [region]" without specifying sub-processor locations; references to outdated Privacy Shield; no mention of TIA; SCCs referenced without specifying module; no mention of supplementary measures.

D5 — Breach Notification
GDPR Art. 33: The controller must notify the supervisory authority without undue delay and, where feasible, not later than 72 hours after becoming aware of a breach, unless the breach is unlikely to result in a risk to rights and freedoms. If notification exceeds 72 hours, it must be accompanied by reasons for the delay. GDPR Info
GDPR Art. 33(2) — Processor to Controller: The processor shall notify the controller without undue delay after becoming aware of a personal data breach. GDPR Info Note: GDPR prescribes no explicit time limit for processor-to-controller notification other than "without undue delay."
GDPR Art. 33(4): The GDPR recognizes that complete information may not always be available within 72 hours, and allows phased reporting — the initial notification can be supplemented with further information as it becomes available. Glocertinternational
GDPR Art. 34 — Individual notification: Individual notification triggers when a breach is likely to result in a HIGH risk to rights and freedoms — a higher threshold than supervisory authority notification. Unlike authority reporting, there is no specific 72-hour deadline, but organizations cannot delay unnecessarily once the high-risk determination is made. GDPRLocal
Art. 33(3) required content:

Nature of the breach (categories and approximate numbers of individuals/records)
DPO or contact point details
Likely consequences
Measures taken or proposed to address and mitigate

CCPA/CPRA: No specific breach notification timeframe in the CCPA itself — California relies on the existing California Civil Code §1798.82 which requires notification "in the most expedient time possible and without unreasonable delay." No 72-hour equivalent exists.
Enforcement: Failure to notify is itself a separate violation carrying potential fines up to €10 million or 2% of global annual turnover. Glocertinternational Meta was fined €251 million in December 2024 for a 2018 breach affecting 29 million users, where the DPC found Meta failed to implement privacy by design, did not fully document the breach, and submitted incomplete notifications — violations of Arts. 25 and 33. CookieYes
Red flags in DPAs: Notification timeframes like "within a reasonable period" or "promptly" without a defined SLA; no obligation to assist with the controller's 72-hour clock; no commitment to provide Art. 33(3) content.
Best practice: Vendor DPAs should commit to notifying the controller within a specific window (24–48 hours is emerging best practice) to leave the controller time to assess and meet the 72-hour regulatory deadline.

D6 — AI/ML Data Usage
EU AI Act (Regulation 2024/1689) — the new regulatory layer:
This is the dimension with the most active regulatory development. Key articles:
Art. 10 — Data Governance for High-Risk AI: High-risk AI systems must be developed using high-quality datasets for training, validation, and testing. These must be managed properly, considering data collection processes, data preparation, potential biases, and data gaps. Datasets should be relevant, representative, error-free, and complete as much as possible. EU Artificial Intelligence Act
Special categories of personal data used for bias correction must be subject to strict controls — secured, protected, with documentation of access, deleted once the bias has been corrected or retention period ends, whichever is first. EU Artificial Intelligence Act
Art. 53 — GPAI Model Obligations: All GPAI model providers must provide technical documentation, instructions for use, comply with the Copyright Directive, and publish a summary about the content used for training. EU Artificial Intelligence Act
Under Art. 53(1)(d), GPAI providers must publish a detailed summary of training data, identify large training datasets individually, and indicate whether they obtained commercially licensed content. WilmerHale
Art. 50 — Transparency for all AI: Art. 50 sets out transparency obligations for providers and deployers of certain AI systems, including generative and interactive AI systems. People interacting with AI systems must be notified that they are interacting with AI. European Commission
Penalties: The highest penalties apply to banned AI systems and can reach €35 million or 7% of global annual turnover. Lowenstein Sandler LLP For GPAI-specific violations, fines can reach up to 3% of global annual turnover or €15 million. Securiti
GDPR intersection: The EU AI Act does not replace GDPR — they operate in parallel. A vendor using customer data for AI training needs a lawful basis under GDPR and must comply with the AI Act's data governance provisions. The CJEU's Schrems v Meta ruling on data minimization directly limits the scope of permissible AI training on personal data.
Red flags: Vendor privacy policy says "we may use data to improve our AI models" without specifying opt-out mechanisms, legal basis, or what data categories; no mention of AI Act obligations for high-risk use cases; no training data governance disclosures.

D7 — Retention and Deletion
GDPR Art. 5(1)(e) — Storage limitation: Data must be kept in a form permitting identification of data subjects for no longer than necessary for the purposes for which it is processed.
GDPR Art. 17 — Right to erasure: Controllers must erase data without undue delay when it's no longer necessary, consent is withdrawn, the subject objects, or processing was unlawful.
Art. 28(3)(g) requires the DPA to specify deletion or return at contract end.
The principle of data minimization also has a temporal element — requiring the controller to limit the period of data collection to what is strictly necessary for the pursued purpose. GDPRhub
CCPA/CPRA: Once the job is done, the service provider should delete the data, except as required to meet legal obligations. TerraTrue The CPRA added the right to know specific retention periods.
Red flags: "Data may be retained as required by applicable law" without specifying which law or for how long; no defined retention schedule; no mechanism for confirming deletion; DPA says "commercially reasonable efforts to delete."

Key Framework Conflicts to Encode in Bandit
AreaGDPRCCPA/CPRAEU AI ActBreach timeline72 hours to SA; "without undue delay" processor→controllerNo specific timeline (CA Civil Code: "most expedient time possible")Serious incident reporting for GPAI (details TBD in implementation)Sub-processor controlPrior authorization + right to objectNotification + same contractual flow-downValue chain responsibilities (Art. 25)AI training dataRequires lawful basis under Art. 6; minimization appliesConsent/opt-out for "sale" or "sharing"Art. 10 data governance + Art. 53 training data summaryTransfer mechanismsAdequacy, SCCs, BCRs + TIANo equivalent cross-border framework (some state laws emerging)N/A (follows GDPR for personal data)Penalty ceiling€20M / 4% global turnover$2,663–$7,988 per violation (inflation-adjusted 2024)€35M / 7% global turnoverDPA required?Yes, mandatory under Art. 28Yes — failure to have a compliant contract results in the data transfer being deemed a "sale" or "sharing" Privacy WorldFollows GDPR + value chain contracts

Implementation Notes for Scoring
For your 1–5 scale, the regulatory research suggests natural breakpoints:

1 (Absent): No DPA, no privacy policy disclosure on the topic, or language that contradicts the requirement
2 (Deficient): Addresses the topic but with vague language, missing mandatory elements, or outdated mechanisms (e.g., Privacy Shield references)
3 (Minimum compliant): Meets the literal regulatory requirement but with generic/template language and no evidence of tailoring
4 (Strong): Exceeds minimum with specific timeframes, mechanisms, and operational detail (e.g., 24-hour breach notification SLA, published sub-processor list with change notification)
5 (Gold standard): Best practice with proactive commitments — contractual SLAs with teeth, TIA documentation, AI training data governance, annual audit provisions, and specific regulatory citations
]

---

## Search 2 — Enforcement Cases  
[D5 — BREACH NOTIFICATION: Enforcement-Derived Scoring Criteria
What regulators have actually fined
Meta — €251M (Ireland, Dec 2024): Fined for a 2018 breach affecting 29 million users. The DPC found Meta failed to fully document the breach and submitted incomplete notifications — violations of Art. 25 (privacy by design) and Art. 33 (breach notification). The key failure wasn't just the breach itself but the quality of the notification response.
General enforcement pattern: Failure to comply with the lawfulness, fairness and transparency principle remains the top enforcement priority across European jurisdictions, and fines for breach of the integrity and confidentiality principle and Art. 32 security of processing continue to feature across all jurisdictions. DLA Piper
Specific language failures (red flags for scoring)
Processor agreements should specify breach notification timeframes. Many controllers require faster notification than "without undue delay" — commonly 24 or 48 hours. Glocertinternational
Score 1 language — absent or non-compliant:

No breach notification clause in the DPA at all
"Vendor will notify customer of security incidents as required by law" (no specifics)
No commitment to assist with the controller's Art. 33 obligations

Score 3 language — minimum compliant:

"Processor shall notify controller without undue delay after becoming aware of a personal data breach" (mirrors GDPR Art. 33(2) language verbatim, but adds nothing)
No specific SLA timeframe
Mentions notification but doesn't commit to providing Art. 33(3) content (nature, approximate numbers, likely consequences, measures taken)

Score 5 language — gold standard:

Specific SLA: "Processor shall notify controller within 24 hours of becoming aware of a confirmed or suspected personal data breach"
Commits to providing all Art. 33(3) required content elements
Includes obligation to preserve evidence and assist with regulatory notifications
Defines "awareness" trigger clearly
Addresses phased reporting per Art. 33(4)
Covers both confirmed breaches and suspected incidents

The critical gap: Processor-to-controller timeline
GDPR Art. 33(2) says "without undue delay" for processor-to-controller notification but prescribes no hours. The 72-hour clock runs on the controller from when the controller becomes aware. This means if a vendor DPA only says "without undue delay" and the vendor takes 48 hours to notify, the controller has only 24 hours left. Best-practice DPAs specify a tighter window precisely because of this arithmetic.

D2 — SUB-PROCESSOR MANAGEMENT: Enforcement-Derived Scoring Criteria
The CRITEO case — €40M (France, June 2023)
This is the single most instructive enforcement action for sub-processor/partner management scoring. The CNIL found that Criteo failed to implement adequate measures to ensure that its partners, acting as joint controllers, properly collected users' consent before placing cookies on user terminals. Globalprivacyblog
The critical finding: A contractual obligation on the partner to obtain consent did not go far enough — the CNIL found Criteo hadn't put any contractual assurances in place requiring partners to provide proof of consent on request, and hadn't undertaken any audit of its partners to stress test the consent they claimed to obtain. Lewis Silkin
The new standard set by CRITEO: Partners must "promptly provide Criteo, upon request and at any time, with proof that the consent of the data subject has been obtained by the partner." Accountability is the new king — regulators are no longer willing to allow companies to rely on paper assurances. AdMonsters
There is a very high bar set by the CNIL when it comes to verification and audit of partner consent practices. The expectation is that intermediaries who rely on consent must actively check the validity of such consents. Bristows
Scoring implications derived from CRITEO
Score 1:

No sub-processor list
No notification mechanism for sub-processor changes
DPA is silent on sub-processing entirely

Score 3:

Sub-processor list exists (possibly buried in a URL reference)
General authorization with notification of changes
Standard contractual flow-down clause
BUT: No audit mechanism, no proof-of-compliance requirement, no specified objection period

Score 5:

Published, maintained sub-processor list with change-log
Specific notification period before new sub-processor engagement (e.g., 30 days)
Explicit right to object with contractual consequences (ability to terminate if objection not resolved)
Contractual requirement that sub-processors provide proof of compliance on request
Audit rights extending to sub-processors
Same Art. 28(3) obligations contractually flowed down to each sub-processor
Processor retains full liability for sub-processor failures per Art. 28(4)


D6 — AI/ML DATA USAGE: Enforcement-Derived Scoring Criteria
FTC Algorithmic Disgorgement — The precedent cascade
This is the most aggressive enforcement posture in the AI data usage space and it directly shapes what vendor policies should say.
The timeline of escalating FTC enforcement:
The Biden-era FTC, since Cambridge Analytica (2019), regularly deployed model deletion as a remedy: in its orders in Everalbum (2021), Weight Watchers (2022), Ring (2023), Edmodo (2023), Rite Aid (2024), and Avast (2024). Technology Law
Key enforcement specifics:
Everalbum (2021): The company had allegedly violated Section 5(a) of the FTC Act by promising customers it would only use facial recognition on users' content if they opted in, and that it would delete users' content if they deactivated their account, but did not adhere to either promise. Debevoisedatablog The settlement required Everalbum to "delete or destroy any Affected Work Product" — defined as "any models or algorithms developed in whole or in part using" illegally collected user data — within ninety days. Mintz
Weight Watchers/Kurbo (2022): The settlement required Weight Watchers to delete or destroy any personal data collected from children without consent, as well as any models or algorithms developed using that personal information. It also prohibits Weight Watchers from "disclosing, using or benefitting from" any of the information obtained prior to settlement. Debevoisedatablog
Amazon Alexa ($25M penalty, 2023): Amazon was required to pay $25M in civil penalties for COPPA violations and delete illegally retained Alexa voice recordings of children. The broader FTC complaint included allegations that Amazon retained voice recordings beyond stated retention periods and used them to train AI models without adequate consent. Anonym
FTC's explicit position on retroactive AI data usage
On February 13, 2024, the FTC published a blog reminding companies that it may be unfair or deceptive for a company to give themselves permission to expand their use of consumer data — for example, sharing consumers' data with third parties or using data for AI training — without getting consent. Retroactive material changes to a privacy policy require affirmative consent. Loeb
The FTC stressed that collecting data for one purpose and then processing it for AI models may be an unfair or deceptive practice. The FTC conditioned settlement on restrictive remedies, in one case requiring the deletion of the collected data and any algorithms derived from it, and in the other case prohibiting data use in future algorithms. Latham & Watkins
There is no AI exemption from the laws on the books. Like all firms, model-as-a-service companies that deceive customers or users about how their data is collected — whether explicitly or implicitly, by inclusion or by omission — may be violating the law. Federal Trade Commission
The data provenance enforcement angle
"One of the biggest opportunities of this use of disgorgement is you're forcing a data provenance and data governance practice because if you don't track where everything is and what tweaks you've made with what sorts of data then the enforcement agency is likely not going to be particularly charitable. It's more like they're going to have an overinclusive set of data and of algorithms that they have to delete." CyberScoop
The FTC's enforcement actions establish practical guidance: Organizations must be able to document what personal data was used to train AI models, whether consent was adequate for that training use, and what retention period applied. Anonym
CRITEO AI training gap — GDPR side
Improvement of Criteo's technologies through machine learning constituted a separate purpose from the general provision of advertising services, and as such needed to be called out in the privacy notice. Bristows This is a direct regulatory finding that "we use data to improve our services" is insufficient when AI/ML training is involved — it must be disclosed as a distinct purpose.
Scoring implications for D6
Score 1:

No mention of AI/ML data usage at all in privacy policy or DPA
OR: Vague language like "we may use data to improve our products and services" that doesn't distinguish AI training
OR: Retroactive policy changes to permit AI training without consent

Score 3:

Acknowledges AI/ML usage exists
States data "may" be used for model training
Provides an opt-out mechanism but it's buried or burdensome
No specifics about which data categories, what models, or how long training data is retained
Doesn't address algorithmic disgorgement obligations

Score 5:

Explicit, separate disclosure of AI/ML training as a distinct processing purpose
Specifies which data categories are used for training and which are excluded
Affirmative opt-in (not just opt-out) for AI training on customer data
Contractual commitment that customer data will not be used to train models serving other customers
Data provenance documentation commitments
Retention period specific to training data
Commitment to delete derived models/algorithms if underlying data consent is withdrawn
Addresses both GDPR Art. 6 legal basis AND FTC fair practice requirements


D7 — RETENTION AND DELETION: Enforcement-Derived Scoring Criteria
The Netflix case — €4.75M (Netherlands, Dec 2024)
This is the most instructive recent enforcement for retention-specific language failures.
The Dutch DPA identified deficiencies in four key areas, including retention periods: Netflix did not communicate how long it retained customer data or the criteria used to determine retention periods. Stibbe
The specific language Netflix used that was found insufficient: Netflix's privacy policy vaguely stated that data is retained "as required or permitted by applicable laws and regulations." Steel-eye
More broadly, the AP found that while Netflix listed the data it collects and the purposes for its use, it failed to transparently link specific data categories to their corresponding processing purposes. For instance, it did not make clear what specific data it uses for its recommendation engine, for audience analysis, or for fraud prevention. Steel-eye
Netflix argued its privacy statement was adequate because the GDPR's transparency obligations are "open norms" which allow for a degree of freedom in how information is presented Steel-eye — the DPA rejected this outright.
The Amazon France case — €32M (CNIL, Dec 2023)
The CNIL criticized indicators like tracking scanner inactivity and fast scanning, considering them invasive and unnecessary. Data was retained longer than necessary and used for employee evaluations, scheduling, and training, violating data minimization, lawful processing, and transparency provisions. Data Privacy Manager
Scoring implications for D7
Score 1:

No retention schedule or period mentioned
"Data retained as permitted by applicable law" (the Netflix failure)
"Data retained indefinitely" or silence on the topic
No deletion mechanism at contract termination

Score 3:

General retention period stated (e.g., "data retained for up to X years")
Mentions deletion at contract end per Art. 28(3)(g)
BUT: No category-specific retention schedules
No link between specific data types and their retention periods
No mechanism for confirming deletion has occurred

Score 5:

Category-specific retention schedules linking data types to purposes to periods
Clear criteria for determining retention periods when exact periods aren't possible
Contractual deletion commitment at end of services with specified timeframe (e.g., "within 30 days")
Certification of deletion upon request
Addresses backup/archive copies explicitly
Covers sub-processor data deletion obligations
Specifies what happens to derived/aggregated data
Addresses AI training data retention separately from operational data


Cross-Cutting Enforcement Pattern: Transparency as the Meta-Requirement
The enforcement data reveals one overarching theme that touches all dimensions:
In November 2024, the Dutch DPA fined a well-known online streaming service €4.75 million for failing to provide clear and complete information in its privacy statement. The DPA found the company's privacy statement lacked transparency on the purposes and legal bases for collecting and using personal data, what personal data was shared with others and why, and security measures when transferring data outside of Europe. Smith Anderson
Non-compliance with general data processing principles is most likely to result in significant fines — five of the ten largest fines were for this violation type. CMS
The most common cause of violations is Art. 5 GDPR, principles relating to processing of personal data. This includes issues like not having a valid legal basis, not being transparent about data processing or data subjects' rights, or processing data for purposes beyond those communicated. Usercentrics
The "Vague Language" Red Flag Taxonomy
From the enforcement actions, here are the specific patterns Bandit should flag as score-reducing:
Red Flag PatternEnforcement PrecedentImpact"as permitted by applicable law" (retention)Netflix €4.75MScore ≤2 on D7"we may use data to improve our services" (AI)CRITEO €40M, FTC guidanceScore ≤2 on D6"we share data with third parties" (no specifics)Netflix €4.75M, WhatsApp €225MScore ≤2 on D2"without undue delay" (breach, no SLA)GDPR minimum, not best practiceScore ≤3 on D5"reasonable efforts to notify" (sub-processors)Below Art. 28(2) standardScore ≤2 on D2Privacy policy contradicts itself on legal basisCRITEO €40MScore ≤2 on D8Purpose decoupled from data categoriesNetflix €4.75MScore ≤2 on D1Retroactive policy change for AI trainingFTC Feb 2024 guidance, EveralbumScore 1 on D6"Data may be retained for legitimate business purposes"Amazon France €32MScore ≤2 on D7

Enforcement-Calibrated Score Boundaries (Summary)
For each of the four dimensions, here's where enforcement actions draw the lines:
The 1-2 boundary: Missing the requirement entirely, or using language that regulators have specifically fined others for (Netflix retention language, CRITEO vagueness, Everalbum-style retroactive AI training).
The 2-3 boundary: Addressing the topic but with generic/template language that mirrors the regulation verbatim without operational specifics. A DPA that says "without undue delay" for breach notification technically meets Art. 33(2) but adds zero operational value.
The 3-4 boundary: Adding operational specifics beyond minimum compliance — a stated timeframe for breach notification, a published sub-processor list, category-specific retention periods.
The 4-5 boundary: Proactive commitments with teeth — contractual SLAs, audit rights, certification of deletion, explicit AI training opt-in, data provenance documentation, and evidence of the vendor actually doing what the policy says (published sub-processor lists with change logs, incident response playbooks, etc.).]

---

## Search 3 — AI/ML Regulations
[REGULATORY FRAMEWORK MAP FOR D6 — AI/ML DATA USAGE
1. EU AI Act (Regulation 2024/1689) — Now Partially In Force
Art. 53(1) — Four Core GPAI Provider Obligations:
Article 53(1) establishes four core obligations: documentation and transparency duties, policies on copyright law, and a training data summary. Bird & Bird
Specifically:

(a) Technical documentation — Providers must complete a detailed model documentation form covering technical properties, training, energy consumption, and intended use. Documentation will be drawn up for each model version and will remain available for 10 years. Latham & Watkins
(b) Downstream provider transparency — GPAI providers can be required to provide additional information to downstream providers within 14 days from request if it is "relevant for its integration" and enables downstream providers to comply with their AI Act obligations. Latham & Watkins
(c) Copyright compliance policy — Providers must implement a policy ensuring compliance with EU copyright law, with particular focus on respecting opt-outs under Article 4(3) of the CDSM Directive. Providers must use state-of-the-art technologies to identify and exclude protected content. Arnold & Porter
(d) Training data summary — Article 53(1)(d) mandates that all GPAI model providers create and publicly release a "sufficiently detailed public summary of the content used for the training of the model." Steptoe

The Training Data Summary Template (published July 24, 2025):
The Training Data Disclosure Template sets out mandatory publication obligations requiring clear public documentation on: the origin and nature of training datasets, including whether data was scraped, licensed, synthetic, or user-provided; data modalities and curation processes; bias mitigation methods applied during model training; and copyright and IP compliance. This transparency obligation is legally binding, not optional. MediaLaws
Providers must identify large training datasets individually, while smaller datasets may be described in aggregate. They must indicate whether they obtained commercially licensed content via licensing agreements and specify whether training data includes web-scraped content, including a list of the top 10% of domain names used. WilmerHale
Timeline: The requirement to publish the training data summary took effect starting August 2, 2025. Providers of GPAI models released before that date must ensure the summary is published no later than August 2, 2027. Securiti
Update cadence: GPAI model providers are required to update summaries at least every six months or whenever there are material changes, such as model fine-tuning or additional training. Securiti
Enforcement: Non-compliance can result in substantial penalties, with fines reaching up to 3% of a provider's total global annual turnover or €15 million, whichever is higher. Securiti For broader AI Act breaches, Article 99 enables penalties up to €35 million or 7%. MediaLaws
Art. 10 — Data Governance for High-Risk AI Systems: Requires training, validation, and testing datasets to be subject to appropriate data governance practices, including documenting data collection processes, the origin of data, bias detection measures, and data gaps. Special categories of personal data used for bias correction must be deleted once the correction is made or the retention period ends.
Art. 50 — Transparency for All AI Systems: People interacting with AI must be informed they are interacting with AI (unless obvious). Providers of AI-generated content must facilitate identification and mark content in machine-readable format.
Code of Practice (endorsed August 1, 2025): The rapid adoption of the GPAI Code of Practice by nearly all major global AI providers underscores its central importance as the de facto industry standard. Bird & Bird Non-signatories face higher scrutiny: A provider that ignores the Code and develops its own approach carries considerable risk, as the provider must then justify its compliance measures from the ground up and can expect a higher degree of scrutiny from enforcement authorities. Bird & Bird

2. GDPR — The Legal Basis Problem for AI Training
The OpenAI/ChatGPT enforcement (Italy, Dec 2024 — €15M):
This is the single most important enforcement action for D6 scoring. The Garante found that OpenAI had processed user data "to train ChatGPT without first identifying an adequate legal basis," directly violating the GDPR's transparency principle and its obligation to inform users. Lewis Silkin
The specific violations found:

OpenAI had not identified a lawful basis for training ChatGPT pre-launch, nor had it identified an appropriate lawful basis for processing from launch on November 30, 2022 until March 30, 2023. Dataprotectionreport
As to non-users, no privacy notice on the processing of their data for the purpose of training ChatGPT was available. Dataprotectionreport For users, the privacy notice was available only in English language and certain paragraphs, such as the purposes of processing, were too broad and unclear. Dataprotectionreport
OpenAI also failed to inform the Garante of a breach it experienced on March 20, 2023, which exposed chat histories and payment information of ChatGPT Plus subscribers during a nine-hour window. Lewis Silkin
OpenAI has not provided for mechanisms for age verification, which could lead to the risk of exposing children under 13 to inappropriate responses. The Hacker News

Remedies beyond the fine: OpenAI was ordered to carry out a six-month communication campaign on radio, television, newspapers, and the internet to promote public understanding of how ChatGPT collects and uses data, including making users and non-users aware of how to oppose their personal data being used for AI training. The Hacker News
The legal basis question remains unresolved at EU level. The GDPR provides six possible legal bases under Art. 6. For AI model training, only two are realistic: consent or legitimate interests. OpenAI currently relies on legitimate interests, which still requires honoring data subject objections under Art. 21.
The EDPB weighed in: The EDPB also emphasised the need for controllers deploying the models to carry out an appropriate assessment on whether the model was developed lawfully. Dataprotectionreport This means downstream deployers (i.e., vendors using third-party AI models) have their own obligation to verify the lawfulness of the underlying model's training data.

3. FTC Enforcement — Algorithmic Disgorgement and the Purpose Limitation Doctrine
The core FTC principle (February 2024 blog post): It may be unfair or deceptive for a company to retroactively expand its use of consumer data for AI training without affirmative consent. This applies even when the expansion is disclosed through a privacy policy update.
The algorithmic disgorgement precedent chain (from Search 2 — repeated here for completeness as it's central to D6):
The FTC has ordered model/algorithm deletion in: Cambridge Analytica (2019), Everalbum (2021), Weight Watchers (2022), Ring (2023), Edmodo (2023), Rite Aid (2024), and Avast (2024). The common thread: data collected for one purpose (photos, children's health, home security) was used to train AI models without adequate notice or consent.
FTC's explicit AI guidance (January 2024): Model-as-a-service companies that deceive customers about how data is collected — whether explicitly or implicitly, by inclusion or by omission — may be violating the law. There is no AI exemption from existing laws.
Key FTC practical requirements derived from enforcement:

Training data transparency: document what personal data was used, whether consent was adequate, and what retention period applied
Purpose limitation: data collected for one purpose cannot be repurposed for AI training without separate disclosure and consent
Vendor accountability: the deploying organization is responsible for its vendor's AI data practices


4. US State AI Laws — Emerging Compliance Patchwork
California CCPA/CPRA ADMT Regulations (finalized July 2025):
In July 2025, the CPPA adopted final regulations governing automated decision-making technology (ADMT), privacy risk assessments, and cybersecurity audits under the CCPA. Coblentz Law
Key requirements:

Businesses are subject to ADMT obligations when the technology is used to make "significant decisions" affecting financial services, employment, housing, education, or healthcare, or when they engage in certain types of profiling or train models for such use cases. Coblentz Law
The revised rules allow businesses to integrate ADMT disclosures into existing notices at collection rather than requiring standalone pre-use notices. Coblentz Law
Consumers must be able to opt out of ADMT use for significant decisions, extensive profiling, or training purposes. Workforcebulletin
From January 1, 2027, businesses using ADMT for significant decisions must provide pre-use notices explaining the purpose, data use, decision logic, and opt-out rights. Two or more opt-out channels must be offered. www.lightbeam.ai

Colorado AI Act (SB 24-205) — delayed to June 30, 2026:
Colorado has postponed implementation of its landmark AI law until June 2026, following failed negotiations during the legislature's special session. Seyfarth Shaw LLP
Key requirements when effective:

Deployers and developers must disclose the reasons behind adverse consequential decisions and allow consumers to correct inaccuracies or appeal. White & Case LLP
Deployers must make a publicly available statement summarizing the types of high-risk AI systems deployed, how the deployer manages known risks of algorithmic discrimination, and the nature, source, and extent of information collected and used. Colorado General Assembly
Deployers must disclose to the attorney general the discovery of algorithmic discrimination within 90 days. Colorado General Assembly

Illinois HB 3773 (effective January 1, 2026):
The Illinois statute requires disclosure to employees when employers use AI for employment decisions. Seyfarth Shaw LLP

5. The CRITEO Precedent — AI Training as a Separate Processing Purpose
From Search 2, this finding directly shapes D6 scoring: The CNIL found that Criteo's use of data to improve its technologies through machine learning constituted a separate purpose from its general advertising services and needed to be independently disclosed in the privacy notice. A vendor that buries AI training under "improving our services" is directly contradicting this enforcement finding.

D6 SCORING RUBRIC — Enforcement-Grounded Criteria
Score 1 — Absent or Non-Compliant
Indicators (any of these = Score 1):

No mention of AI/ML data usage anywhere in privacy policy or DPA
Vague catch-all language like "we may use data to improve our products and services" with no AI-specific disclosure (the exact pattern found insufficient in CRITEO and OpenAI enforcement)
Retroactive privacy policy change adding AI training permission without affirmative consent (directly contradicts FTC February 2024 guidance)
Evidence that vendor trains models on customer data with no disclosure at all (the Everalbum/Weight Watchers pattern that triggers algorithmic disgorgement)
Privacy policy available only in English for EU-facing services (OpenAI violation finding)

Regulatory basis: GDPR Arts. 5(1)(a), 6, 12, 13; FTC Act Section 5; EU AI Act Art. 53(1)(d)
Score 2 — Materially Deficient
Indicators:

AI/ML usage mentioned but only in generic terms ("we use AI to improve our services")
AI training listed as a purpose but bundled with other purposes, not separately identified (violates CRITEO finding)
No specification of which data categories are used for AI training
No disclosure of legal basis for AI training specifically
Opt-out for AI training exists but is buried, difficult to find, or burdensome (FTC has flagged opt-out burdensomeness as a concern)
No mention of whether customer data is used to train models that serve other customers
DPA silent on AI/ML usage entirely

Score 3 — Minimum Compliant
Indicators:

AI/ML training disclosed as a distinct processing purpose, separate from service delivery
Legal basis identified for AI training (e.g., legitimate interests under Art. 6(1)(f))
Opt-out mechanism available and functional
General description of data types used for training
DPA addresses AI/ML at a high level (e.g., "processor will not use customer data for AI training without controller's consent")
BUT: No specifics on which models, no training data governance disclosures, no data provenance documentation, no commitment regarding derived models/algorithms

Regulatory basis: Meets letter of GDPR Arts. 5, 6, 12, 13; aligns with FTC notice expectations; partial compliance with EU AI Act Art. 53 direction of travel
Score 4 — Strong
Indicators:

AI/ML training clearly disclosed as a distinct purpose with specific legal basis
Specifies which data categories are used and which are excluded from AI training
Opt-out mechanism is prominent, accessible, and easy to use
DPA contains an explicit, affirmative clause: "Processor shall not use Customer Data to train, improve, or develop AI/ML models unless explicitly authorized in writing by Controller"
Addresses customer data segregation — commitment that one customer's data is not used to train models serving other customers
Retention period specified for training data distinct from operational data
Provides information about human oversight of AI systems
Addresses downstream deployer obligations (aligning with EDPB guidance that deployers must verify lawfulness of underlying model training)
Published information about AI systems used in service delivery

Regulatory basis: Exceeds GDPR minimum; aligns with FTC algorithmic disgorgement prevention; anticipates EU AI Act Art. 53 compliance; meets Colorado AI Act developer disclosure requirements
Score 5 — Gold Standard Best Practice
Indicators — must demonstrate ALL of the following:

Explicit separate disclosure of AI/ML training as a distinct processing purpose with identified legal basis (GDPR Art. 6 + legitimate interests assessment or consent)
Categorical specificity: identifies which data categories are used for training, which are excluded, and how personal data is handled vs. anonymized/aggregated data
Affirmative opt-in for customer data use in AI training (not merely opt-out) — strongest defensible position given OpenAI enforcement and FTC guidance
Customer data segregation commitment: contractual guarantee that customer data will not be used to train models serving other customers (multi-tenant isolation)
Data provenance documentation: commitment to maintain records of what data was used in which models (directly addresses the FTC's algorithmic disgorgement concern — "if you don't track where everything is and what tweaks you've made with what sorts of data then the enforcement agency is likely not going to be particularly charitable" CyberScoop)
Training data retention schedule: specifies how long training data is retained, when it is deleted, and how derived model weights are handled upon data deletion request
Algorithmic disgorgement readiness: commitment to delete derived models/algorithms if underlying data consent is withdrawn or if data was processed unlawfully (aligned with FTC remedy precedent and GDPR right to erasure implications for AI)
EU AI Act alignment: training data summary published or available per Art. 53(1)(d) template; technical documentation maintained per Art. 53(1)(a); downstream provider information available within 14 days per Code of Practice
Transparency about AI in service delivery: disclosure of which AI systems are used, what decisions they inform, and how customers can request human review
Bias and fairness commitments: documentation of bias mitigation in training data per EU AI Act Art. 10 requirements
Regular update cadence: commitment to update AI disclosures at minimum every six months or upon material changes (matching EU AI Act Art. 53(1)(d) template requirement)
DPA contains all of the above as binding contractual commitments, not merely aspirational policy language

Regulatory basis: Full compliance with GDPR + EU AI Act + FTC enforcement expectations + Colorado AI Act developer disclosure requirements + CPRA ADMT opt-out rights

KEY REGULATORY CONFLICTS TO ENCODE
IssueEU (GDPR + AI Act)US (FTC + State Laws)Conflict/GapLegal basis for AI trainingMust identify Art. 6 basis; consent or legitimate interests (OpenAI precedent)No federal requirement for specific legal basis, but FTC requires notice/consent for repurposing dataEU requires affirmative legal basis; US relies on notice + unfairness doctrineTraining data disclosureMandatory public summary per Art. 53(1)(d) template (binding Aug 2025)No federal equivalent; CO AI Act requires developer documentation; CA ADMT regs require purpose disclosureEU far more prescriptive; US is enforcement-drivenOpt-out vs. opt-inArt. 21 right to object (for legitimate interests basis); EDPB emphasizes data subject controlCPRA: opt-out right for ADMT training; FTC: affirmative consent for repurposingBoth offer opt-out, but FTC guidance on repurposing effectively requires opt-in for new AI usesAlgorithmic disgorgementNo explicit GDPR mechanism, but right to erasure (Art. 17) has implications; EDPB exploringFTC has ordered model deletion in 7+ settlements since 2019US has established remedial precedent; EU lacks explicit mechanism but direction of travel is alignedDownstream deployer liabilityEDPB: deployers must verify lawfulness of model training data; AI Act value chain responsibility (Art. 25)Rite Aid: FTC held deployer (not developer) responsible for AI system accuracy and biasBoth hold deployers accountable, but through different mechanismsPenaltiesGDPR: €20M / 4%; AI Act: €35M / 7% (prohibited) or €15M / 3% (GPAI)FTC: model deletion + per-violation fines; CO: $20K per violation; CA: $2,663-$7,988 per violationEU penalties financial; US remedies more operational (model deletion)

ENFORCEMENT TIMELINE — Key Dates for D6
DateEventImpact on Scoring2019–2024FTC algorithmic disgorgement in 7+ casesEstablishes model deletion as standard remedyDec 2024OpenAI fined €15M by Italian DPAFirst major GDPR fine specifically for AI training data practicesJul 2025CA CPPA adopts final ADMT regulationsOpt-out rights for AI training; pre-use notices from Jan 2027Aug 2, 2025EU AI Act GPAI obligations apply to new modelsArt. 53 training data summaries mandatoryJan 1, 2026Illinois AI employment disclosure law effectiveEmployer AI notice requirementsJun 30, 2026Colorado AI Act effective date (current)Developer documentation + consumer disclosure requirementsAug 2, 2026EU AI Act enforcement powers for GPAI applyAI Office can verify compliance and issue corrective measuresAug 2, 2027Pre-existing GPAI models must comply with Art. 53Full EU AI Act training data transparency deadline

RED FLAG LANGUAGE — Specific Phrases That Should Trigger Score Reduction
Phrase in Vendor PolicyWhy It's a Red FlagMaximum Score"We may use your data to improve our products and services"CRITEO: ML training must be disclosed as separate purpose; OpenAI: too broad and unclear2"By using our service, you consent to AI training"Bundled consent is not freely given (GDPR Art. 7); FTC views as insufficient for repurposing2"We use industry-standard AI practices"No specificity; doesn't meet Art. 53(1)(d) or FTC transparency expectations2"Data may be used for machine learning in anonymized form"Must specify how anonymization is achieved; AI models can re-identify data; doesn't address training data provenance3No AI/ML clause in DPA at allGiven OpenAI enforcement and FTC guidance, silence on AI in a DPA is a gap1"Customer data will not be used for AI training" (policy) but DPA is silentConflict between policy and contractual terms; DPA controls in dispute2"We reserve the right to update this policy to reflect new uses of AI"Directly contradicts FTC Feb 2024 guidance on retroactive changes1

GOLD STANDARD LANGUAGE — What a Score 5 DPA Clause Looks Like
For reference when calibrating Bandit, here's the type of language that should score 5 on D6:

"Processor shall not use, access, or process Customer Data or any derivative thereof for the purpose of training, improving, fine-tuning, or developing any artificial intelligence or machine learning model, algorithm, or system, whether for Processor's own use or for the benefit of any third party, unless Controller provides explicit prior written authorization specifying the scope, data categories, duration, and purpose of such use. Processor shall maintain auditable records of all data used in AI/ML model training, including data provenance documentation. Upon termination of authorization or upon Controller's request, Processor shall delete all Customer Data from training datasets and, where technically feasible, retrain or modify affected models to remove the influence of Controller's data. Processor shall not commingle Controller's data with data from other customers for AI/ML training purposes."

This language would satisfy GDPR Art. 28 + Art. 6 legal basis requirements, align with FTC algorithmic disgorgement prevention, meet EU AI Act Art. 53 direction of travel, and address the data provenance documentation that enforcement agencies increasingly expect.]

---

## Search 4 — Industry Frameworks
[Let me build out the framework-level mapping systematically. This requires several targeted searches to get specific control numbers.Synthesized eight dimensions across six major frameworks comprehensivelySynthesized eight dimensions across six major frameworks comprehensivelyConor, here's the complete framework-to-Bandit dimension mapping. I've organized this as a practical crosswalk that directly feeds into your scoring rubric — showing where frameworks align, where they go beyond the regulatory baseline, and where they conflict or leave gaps.

FRAMEWORK OVERVIEW — What Each Brings to the Table
FrameworkTypeAuditable?Privacy-Specific?AI Coverage?ISO 27701 (2019/2025)International standardYes — certifiableYes — PIMS for controllers & processorsYes (2025 edition)SOC 2 Type IIAttestation reportYes — audited by CPAOptional Privacy TSC (P1–P8)Limited — via points of focus updatesNIST Privacy FrameworkVoluntary risk frameworkNo — self-assessedYes — 5 functions, 18 categoriesYes (1.1 update)CSA CAIQ / CCMCloud-specific questionnaire + controlsSelf-attestation or STAR auditPartial — data governance focusEmergingISO 27018Cloud PII processor code of practiceCertifiable (with 27001)Yes — cloud processor focusNoNIST AI RMFAI risk management frameworkNo — voluntaryPartial — privacy as AI risk dimensionYes — primary purpose

DIMENSION-BY-DIMENSION FRAMEWORK MAPPING
D1 — DATA MINIMIZATION
ISO 27701:
Annex A Table A.1 includes controls around purpose limitation, data minimization and storage limitation under the "Privacy by design and by default" control objective. IAPP The standard translates GDPR's qualitative requirements into specific, testable controls. Data minimization becomes documented retention policies and automated deletion. SecurePrivacy
SOC 2 Privacy TSC:
P3: Collection Limitation — Personal information collected is limited to what is necessary. Bright Defense The auditor wants to check limiting form fields to only essential data, restricting analytics to non-sensitive PII, collecting anonymized data where possible, and documenting the purpose of each data point. Sprinto
NIST Privacy Framework:
Data minimization policies specify that only data necessary for disclosed purposes is collected. SecurePrivacy The Control-P function includes data minimization practices. Subcategory CT.DP-P4 addresses selective collection or disclosure of data elements.
ISO 27018: Establishes data minimization as one of its 8 privacy principles, requiring cloud processors to limit collection, use, retention, and disclosure.
Scoring enhancement from frameworks:

Score 3 (regulatory minimum): Vendor states they collect only necessary data — but no documented evidence
Score 4 (framework-aligned): Vendor has documented data inventory linking categories to purposes (ISO 27701 Clause 4, NIST ID.IM-P8), with periodic review
Score 5 (gold standard): Automated enforcement of minimization policies, privacy-by-design documentation, data discovery and classification processes per ISO 27701:2025 Clause 8


D2 — SUB-PROCESSOR MANAGEMENT
ISO 27701 (Annex B — Processor Controls):
PII Processors must: obtain the controller's authorization before using subcontractors; inform the controller of any intended changes to sub-processors; ensure sub-processors follow equivalent privacy controls. Mediate.com
SOC 2:
The guidance references processes and controls outlined in Trust Services Criterion CC9.2 that can help a service organization assess the risks associated when interacting with a vendor or business partner. KSM The updated 2022 guidance specifically identifies subservice organizations and clarifies that a subservice organization is a vendor performing controls necessary to meet service commitments.
NIST Privacy Framework:
The framework emphasizes demonstrating compliance, not just achieving it. SecurePrivacy Subcategory ID.IM-P7 maps data storage locations including third parties. An entity can use the Privacy Framework to consider how to manage privacy risk not only with regard to its own priorities, but also in relation to how its measures affect other data processing ecosystem entities. NIST
CSA CCM: Domain STA (Supply Chain, Transparency, and Accountability) addresses third-party risk, requiring documented assessment of sub-processors' security posture and contractual flow-down of controls.
Where frameworks go beyond GDPR:

ISO 27701 requires documented records of all processors (mirrors Art. 30 ROPA) but adds the requirement for named individuals responsible for sub-processor management
SOC 2 CC9.2 requires ongoing monitoring of vendor relationships, not just point-in-time assessment
NIST emphasizes ecosystem-wide privacy risk, meaning a vendor should consider how their sub-processor choices affect their customers' privacy risk posture

Scoring enhancement:

Score 3: Published sub-processor list, general authorization with notification
Score 4: Above + SOC 2 CC9.2-aligned vendor monitoring program, contractual flow-down with audit rights
Score 5: Above + named sub-processor management owner (ISO 27701), documented sub-processor risk assessments, automated notification of changes, public change log


D3 — DATA SUBJECT RIGHTS
ISO 27701 (Annex A — Controller Controls):
Specific measures include data subject rights: notice, access, correction, erasure, automated decision. CNIL The standard requires developing procedures for all seven data subject rights, creating DSAR tracking systems capturing request receipt, identity verification, data compilation, response delivery, and exemptions. SecurePrivacy
SOC 2 Privacy TSC:
P5: Access — Provides individuals with access to their personal information for review and update. P6: Disclosure and Notification — Personal information is disclosed only as agreed upon or as required by law. P7: Quality — Personal information is accurate and up-to-date. Bright Defense
NIST Privacy Framework:
Control-P function subcategories CT.DM-P1 through P7 specifically address data management capabilities: CT.DM-P1: Data elements can be accessed for review. CT.DM-P2: Data elements can be accessed for transmission. CT.DM-P3: Data elements can be accessed for alteration. CT.DM-P4: Data elements can be accessed for deletion. CT.DM-P5: Data are destroyed according to policy. National Institute of Standards and Technology
Key framework insight for scoring: ISO 27701 sets a measurable target — measurable privacy objectives such as "Respond to 95% of DSARs within 20 days." SecurePrivacy This translates GDPR's "without undue delay" into an operationally testable SLA. Vendors at Score 5 should have defined, measurable DSAR response targets.
Scoring enhancement:

Score 3: Commits to assisting with DSARs per Art. 28(3)(e) — generic language
Score 4: Documented DSAR procedures with defined SLAs, identity verification process, tracking mechanism
Score 5: Measurable targets (ISO 27701), automated DSAR workflow, covers all 7 GDPR rights explicitly, extends to CCPA rights (deletion, correction, opt-out of sale), addresses processor obligations distinctly from controller obligations


D4 — CROSS-BORDER TRANSFER MECHANISMS
ISO 27701:
The standard addresses conditions for data transfer as a specific control area, including privacy by design and by default. CNIL Annex D maps directly to GDPR Chapter V (Arts. 44–50) on international transfers.
SOC 2:
The revised 2022 points of focus address changing legal and regulatory requirements regarding privacy and distinctions related to privacy that may apply in certain ways to a data controller vs. a data processor. KSM However, SOC 2 does not prescribe specific transfer mechanisms — it evaluates whether the vendor's controls address their stated commitments.
ISO 27018: Specifically addresses cloud processor obligations regarding data location and cross-border transfers, requiring disclosure of countries where data may be processed.
CSA CAIQ: Questions DSI-02 and DSI-05 address data residency and data flow mapping, including sub-processor locations.
Key gap: No framework fully replaces the legal analysis required for GDPR Chapter V compliance (adequacy decisions, SCCs, TIAs). Frameworks test whether processes exist to manage transfers, but they don't validate the legal sufficiency of the transfer mechanism itself.
Scoring enhancement:

Score 3: Identifies transfer mechanism (SCCs, DPF certification) — meets GDPR minimum
Score 4: Above + documented TIA per Schrems II requirements, ISO 27018-aligned location disclosure, sub-processor location specificity
Score 5: Above + supplementary measures documented, automated monitoring of adequacy decision changes, contractual commitment to notify of transfer mechanism changes, EDPB Recommendations 01/2020 alignment


D5 — BREACH NOTIFICATION
ISO 27701:
PII Processors must keep audit logs and notify the controller of any legally binding disclosure requests or data breaches. Mediate.com The standard requires documented incident response procedures with named Incident Response Leads.
SOC 2:
The criteria demand timely breach notifications and ongoing monitoring to ensure policies remain effective. BARR Advisory CC7.3 addresses incident response procedures, CC7.4 addresses containment and remediation, and the Privacy criterion P6.1 specifically covers breach notification to data subjects.
NIST Privacy Framework:
Protect-P function includes incident response plans, breach notification procedures, and ensuring data integrity and confidentiality. Hyperproof Incident response procedures establish who is notified, what timelines apply, and what documentation is required when privacy incidents occur. SecurePrivacy
NIST SP 800-122: Provides specific guidance on incident response for breaches involving PII, including preparation, detection and analysis phases.
Where frameworks exceed regulatory minimums:

ISO 27701 requires named individuals responsible for breach response — not just a "team" or "department"
SOC 2 evaluates whether controls actually operated effectively over the audit period (Type II), meaning breach response isn't just a policy but a tested process
NIST goes beyond notification to include ongoing monitoring and continuous improvement of incident response

Scoring enhancement:

Score 3: "Without undue delay" notification commitment (mirrors GDPR Art. 33(2))
Score 4: Specific SLA (24–48 hours), documented incident response plan (NIST-aligned), named response lead (ISO 27701), includes Art. 33(3) content commitment
Score 5: Above + SOC 2 Type II-attested incident response controls, tested and exercised breach response plan, covers both confirmed and suspected incidents, phased reporting per Art. 33(4), addresses sub-processor breach cascade obligations


D6 — AI/ML DATA USAGE
ISO 27701:2025 — The most significant framework development:
The 2025 edition explicitly acknowledges AI-related privacy risks. Any decision affecting individuals made solely by AI must be explainable and subject to human oversight. Organizations must document how automated reasoning complies with applicable privacy law and avoids bias or discrimination. AI models trained on PII must use de-identified, anonymized, or pseudonymized data whenever possible. Mediate.com
NIST AI Risk Management Framework (AI RMF 1.0):
Provides a structured approach to AI risk management across four functions: Govern, Map, Measure, Manage. Specifically addresses AI transparency, explainability, bias, and data governance. The Colorado AI Act explicitly references NIST AI RMF as an acceptable compliance framework.
NIST Privacy Framework 1.1 update:
The 1.1 update explicitly addresses AI privacy risks including inference risks (can the AI infer sensitive attributes from non-sensitive inputs), membership inference (can attackers determine if individuals' data was in the training set), and bias and discrimination. The Control-P and Protect-P functions apply directly — data minimization in training sets, techniques to reduce model memorization, adversarial testing. SecurePrivacy
SOC 2: The 2022 points of focus updates don't explicitly address AI, but CC8.1 (system design/development) and the privacy criteria P4.1 (use, retention, disposal) apply to AI training data practices. SOC 2+ engagements can map controls to AI-specific frameworks like NIST AI RMF.
CSA: The Cloud Security Alliance has published guidance on AI security, but the CAIQ doesn't yet have comprehensive AI data governance questions.
Critical gap: No single framework comprehensively covers the vendor-specific AI data governance questions relevant to D6. You'll need to synthesize:

ISO 27701:2025 for the privacy management system requirements around AI
NIST AI RMF for the risk management structure
EU AI Act Art. 53 for the disclosure requirements
FTC enforcement patterns for purpose limitation

Scoring enhancement:

Score 3: Acknowledges AI usage, basic opt-out mechanism, general data governance statement
Score 4: ISO 27701:2025-aligned AI privacy controls (explainability, human oversight, de-identification preference), NIST AI RMF-aligned risk management, documented AI data governance practices
Score 5: All of Score 4 + EU AI Act Art. 53 training data summary compliance, NIST AI RMF-aligned bias testing, data provenance documentation, customer data segregation commitment, algorithmic disgorgement readiness


D7 — RETENTION AND DELETION
ISO 27701:
The standard requires documented retention policies and automated deletion, covering all systems including backups. SecurePrivacy Additional controls for data controllers include retention times. Additional controls for data processors include ending of processing. DNV
SOC 2 Privacy TSC:
P4: Use, Retention, and Disposal — Personal information is used, retained, and disposed of appropriately. Bright Defense You must use personal data only for disclosed purposes, retain it only as long as necessary, and dispose of it securely. For example, include automated data retention policies, data destruction workflows, review cycles for outdated PII, and internal guidelines that limit secondary data usage. Sprinto
NIST Privacy Framework:
Retention schedules define how long different data categories are kept and when deletion occurs. SecurePrivacy CT.DM-P5: "Data are destroyed according to policy."
Key framework-over-regulation value: Frameworks operationalize the vague GDPR requirement of "no longer than necessary" (Art. 5(1)(e)) into testable controls:

SOC 2 requires evidence of automated retention enforcement
ISO 27701 requires documented retention schedules linked to purposes
NIST requires category-specific retention periods, not blanket statements

Scoring enhancement:

Score 3: General retention period stated, deletion at contract end per Art. 28(3)(g)
Score 4: Category-specific retention schedules (ISO 27701), automated deletion workflows (SOC 2 P4), covers backup copies explicitly
Score 5: Above + certification of deletion upon request, automated retention enforcement attested in SOC 2 Type II, covers derived/aggregated data, addresses AI training data retention separately, periodic review cycle for retention appropriateness


D8 — DPA COMPLETENESS (Art. 28 Alignment)
ISO 27701 — Annex D (GDPR Mapping):
Annex D maps ISO 27701 directly to GDPR Articles 5–49, confirming that its implementation supports compliance with EU privacy law. CompliancePoint This is the most direct framework-to-regulation crosswalk available. A DPA evaluated against ISO 27701's processor controls (Annex B) and mapped through Annex D provides a structured completeness check against all Art. 28 requirements.
SOC 2:
The revised 2022 points of focus address distinctions related to privacy that may apply in certain ways to an organization that is a data controller and in different ways to an organization that is a data processor. KSM SOC 2+ reports can explicitly include GDPR Art. 28 as additional subject matter.
What frameworks add beyond the Art. 28 checklist:

ISO 27701 requires named individuals for each privacy role — not just "the processor shall..."
SOC 2 Type II provides independent attestation that stated controls actually operated effectively
NIST Privacy Framework's Implementation Tiers provide a maturity model for assessing whether DPA commitments are operationally real

Scoring enhancement:

Score 3: DPA addresses all 8 Art. 28(3)(a)–(h) provisions but with generic/template language
Score 4: Above + DPA is tailored to the specific processing context (not boilerplate), addresses CCPA/CPRA service provider requirements alongside GDPR, includes measurable commitments
Score 5: Above + vendor maintains ISO 27701 certification (attesting to operational privacy management), SOC 2 Type II with Privacy TSC (independent attestation of controls), DPA addresses EU AI Act obligations where applicable, includes NIST-aligned maturity indicators


FRAMEWORK CROSSWALK — Control-Level Mapping
Bandit DimensionGDPR ArticleISO 27701 ControlSOC 2 CriterionNIST PF SubcategoryD1 — Data MinimizationArt. 5(1)(c)Annex A — Privacy by design (minimization)P3.1 (Collection Limitation)CT.DP-P4D2 — Sub-processorsArt. 28(2), (4)Annex B — Sub-processor authorizationCC9.2 (Vendor Risk)ID.IM-P7D3 — Data Subject RightsArts. 12–23Annex A — Obligations to PII principalsP5.1 (Access), P5.2 (Correction)CT.DM-P1 through P4D4 — Cross-Border TransfersArts. 44–50Annex A — PII sharing/transferCC9.2 + Privacy P6ID.IM-P7D5 — Breach NotificationArts. 33–34Clause 6.13 (Incident Mgmt)CC7.3, CC7.4, P6.1Protect-P (PR.PO-P)D6 — AI/ML Data UsageArt. 22 + EU AI Act Art. 532025 edition AI controlsCC8.1 + P4.1Control-P (CT.DP-P) + AI RMFD7 — Retention/DeletionArt. 5(1)(e), 17Annex A — Storage limitationP4.2 (Retention/Disposal)CT.DM-P5D8 — DPA CompletenessArt. 28(3)(a)–(h)Annex B (all processor controls) + Annex D mappingCC9.2 + Privacy criteriaGV.PO-P (Governance)

WHERE FRAMEWORKS CONFLICT OR CREATE GAPS
1. Certifiability vs. Operational Reality:
ISO 27701 certification and SOC 2 Type II attestation verify different things. ISO 27701 certifies the management system is in place. SOC 2 Type II attests that specific controls operated effectively over a period. A vendor could have ISO 27701 certification with controls that don't actually work as designed — SOC 2 Type II catches that gap. For Bandit scoring, SOC 2 Type II with Privacy TSC is stronger evidence than ISO 27701 alone.
2. Prescriptiveness Gap:
NIST Privacy Framework is outcome-based (says what to achieve) while ISO 27701 is control-based (says how to achieve it). SOC 2 is evidence-based (proves you did achieve it). For vendor assessment, you want evidence of doing, not just intending — which means SOC 2 Type II attestation and ISO 27701 certification are more valuable than NIST self-assessment.
3. AI Coverage Gap:
Only ISO 27701:2025 and NIST AI RMF meaningfully address AI data governance. SOC 2 and CSA CAIQ have significant gaps here. A vendor could have a clean SOC 2 Type II report while engaging in problematic AI training practices that the audit scope didn't cover. Bandit's D6 scoring will need to go beyond what any single framework tests.
4. US vs. EU Framework Alignment:
SOC 2 and NIST are US-origin frameworks that don't natively map to GDPR concepts like "legal basis for processing" or "data protection by design and default." ISO 27701 Annex D bridges this gap, but a vendor relying solely on SOC 2 may have blind spots on GDPR-specific requirements. Conversely, ISO 27701 doesn't natively address CCPA concepts like "sale" vs. "sharing" or the CPRA contractor classification.
5. The "Certification ≠ Compliance" Problem:
While ISO 27701 doesn't guarantee compliance with any specific law, it provides a framework aligned with major privacy regulations. Glocertinternational This is critical for Bandit scoring: a vendor holding ISO 27701 certification should score higher than one without it, but certification alone shouldn't automatically yield a Score 5 — the DPA language and policy specifics still need independent evaluation.

PRACTICAL SCORING INTEGRATION
For Bandit, here's how to weight framework evidence across dimensions:
Evidence TypeScore ImpactRationaleSOC 2 Type II with Privacy TSC+1 score boost (max 5)Independent attestation of operating controlsISO 27701 certification+1 score boost (max 5)Certified privacy management systemSOC 2 Type II (Security only, no Privacy)+0.5 on D5, D8 onlySecurity controls attested but privacy not evaluatedNIST PF self-assessment claim+0Self-reported, no independent verificationISO 27001 only (no 27701)+0.5 on D5 onlySecurity management attested, privacy not addressedCSA STAR certification+0.5 on D4Cloud security controls verified, limited privacy coverageNo framework certification+0Policy language evaluated on its own merits
These are additive modifiers to the base score derived from policy/DPA language analysis. A vendor with excellent DPA language but no certifications could still score 4. A vendor with ISO 27701 + SOC 2 Privacy TSC but vague DPA language would get a framework boost but should still be flagged for the language gaps.]

---

## Search 5 — DPA Specifics
[THE ART. 28(3) MANDATORY CHECKLIST — What Each Provision Requires In Practice
The Eight Required Provisions
Art. 28(3)(a) — Documented Instructions
What the law says: Processor processes data only on documented instructions from the controller, including regarding international transfers, unless required by law.
What EDPB Guidelines 7/2020 require in practice: The EDPB calls on controllers to add specific and concrete information on how processors are to comply with their GDPR obligations. The EDPB suggests adding procedures and template forms in contracts with processors — for example, setting forth a detailed procedure that would apply in case of a data breach, or who does what in case data subject requests are received. A controller's instructions should also cover international transfers of data outside the EEA. Privacy World
Boilerplate red flag: "Processor shall process personal data in accordance with Controller's instructions." (No specificity on what those instructions are, no instruction template, no mechanism for providing new instructions.)
Gold standard: Instructions documented in an annex, including permitted processing operations, specific data categories, prohibited uses, mechanism for issuing new instructions, and processor obligation to alert controller if instructions appear to infringe data protection law.

Art. 28(3)(b) — Confidentiality
What it requires: Persons authorized to process data must be committed to confidentiality or under a statutory obligation.
EDPB specifics: The Guidelines clarify that this includes both employees and temporary workers. Further, the processor should make the personal data available only to employees on a need-to-know basis. The confidentiality agreement must "effectively forbid the authorised person from disclosing any confidential information without authorisation, and it must be sufficiently broad so as to encompass all the personal data processed on behalf of the controller." Byte Back
Boilerplate red flag: "Processor shall ensure confidentiality." (No mention of scope, no reference to temporary workers/contractors, no need-to-know principle.)
Gold standard: Specifies that all personnel (employees, contractors, temporary workers) with access are bound by confidentiality obligations covering all controller data, operating under need-to-know access, with confidentiality surviving termination.

Art. 28(3)(c) — Security Measures (Art. 32)
What it requires: Processor implements appropriate technical and organizational measures per Art. 32.
EDPB specifics: The data processing agreement should specify the data security measures adopted by the processor, impose an obligation on the processor to obtain the controller's approval before making any changes to the list of security measures, and require a regular review of those measures to allow the controller to assess their appropriateness. Hunton
Boilerplate red flag: Generic language like "reasonable security measures" or "industry-standard protection" provides no enforceable standards. When breaches occur, these vague terms offer no recourse for inadequate security practices. LegalGPS
Gold standard: Specific TOMs listed in an annex (the EC Art. 28 SCCs template requires this level of detail), with change approval process, regular review cycle, and reference to specific standards (e.g., ISO 27001 certification commitment).

Art. 28(3)(d) — Sub-processor Management
What it requires: Prior specific or general written authorization; obligation to inform of changes; opportunity to object.
EDPB specifics: The EDPB recommends that a DPA should include details on the subprocessors' locations, role, proof of implemented safeguards, and the timeframe for approval of new subprocessors. The Data Advisor
The "then what?" problem: Let's suppose the controller objects to a new subprocessor. Then what? The GDPR doesn't tell us, and many DPAs don't either. At one extreme, the DPA terms say the processor will breach the agreement if it uses a subprocessor over the controller's objection. At the other extreme, the controller can object, but it's a toothless objection. VLP Law Group LLP
The market-standard compromise: The "market" solution that has emerged is for the processor to provide notice to the controller of its intent to use a new subprocessor, with a time window (negotiable) within which the controller may object. VLP Law Group LLP The consequence of an unresolved objection should be a termination right for the controller — that's what makes the objection right meaningful.
Boilerplate red flag: General authorization with no list, no notification mechanism, no objection period, no consequences for objection.
Gold standard: Published sub-processor list with locations and roles; 30-day advance notification of changes; explicit right to object; controller termination right if objection unresolved; same Art. 28(3) obligations flowed down to sub-processors; processor retains full liability per Art. 28(4).

Art. 28(3)(e) — Data Subject Rights Assistance
What it requires: Processor assists controller with DSARs by appropriate technical and organizational measures.
EDPB specifics: The details of this assistance should be included in the DPA or in an annex thereto. The EDPB emphasizes that the controller maintains the responsibility of responding to the request although the practical management can be outsourced to the processor. Byte Back
Boilerplate red flag: "Processor shall assist Controller with data subject requests." (No specifics on turnaround time, no defined procedure, no technical capability commitment.)
Gold standard: Defined SLA for processor response to DSAR forwarding (e.g., 5 business days), technical capability to search/extract/delete specific data subject records, documented escalation procedure, coverage of all GDPR Chapter III rights.

Art. 28(3)(f) — Arts. 32–36 Compliance Assistance
What it requires: Processor assists with security obligations, breach notification, DPIAs, and prior consultation.
EDPB specifics: These obligations cover Art. 32 (security), Art. 33 (SA notification), Art. 34 (data subject notification), Art. 35 (DPIA), and Art. 36 (prior consultation). Byte Back
This is where D5 and D8 intersect: The breach notification commitment in the DPA is the primary evidence for D5 scoring. A DPA that merely says "Processor shall notify Controller of breaches" fails both D8 and D5.
Boilerplate red flag: Generic cross-reference to "obligations under Articles 32-36" with no operational specifics.
Gold standard: Specific breach notification SLA (24–48 hours), commitment to provide Art. 33(3) content elements, DPIA cooperation clause, prior consultation support.

Art. 28(3)(g) — Deletion/Return at Termination
What it requires: At the choice of the controller, delete or return all personal data after processing ends, and delete existing copies.
This is where D7 and D8 intersect: The retention/deletion commitment is contractually evidenced here. A DPA that says "data may be retained as required by law" without further specification fails both D8 and D7.
Boilerplate red flag: "Processor shall delete data at contract end." (No timeframe, no certification, no mention of backups, no provision for return option.)
Gold standard: Specified timeframe for deletion/return (e.g., 30 days), certification of deletion upon request, explicit treatment of backup copies and their deletion schedule, specifies what happens to derived/aggregated data, addresses AI training data separately.

Art. 28(3)(h) — Audit and Compliance Demonstration
What it requires: Processor makes available all information necessary to demonstrate compliance and allows for/contributes to audits and inspections.
EDPB specifics: The processor must be able to demonstrate compliance, not just assert it. This includes allowing both information-based compliance checks and physical audits/inspections.
The practical tension: Processors want to limit the scope and timing of audits. The limitations that processors propose typically include advance notice, compliance with the processor's security/confidentiality requirements, and sometimes reimbursement of expenses. Since the GDPR's audit provision initially refers to making available "all information necessary to demonstrate compliance," it's reasonable that, as an initial step, the processor provides compliance documentation first, with on-site audit as a follow-up if documentation is insufficient. VLP Law Group LLP
Boilerplate red flag: "Processor shall make information available upon reasonable request." (No audit right, no inspection right, no defined process.)
Gold standard: Right to both documentation-based and on-site audits; specified notice period; reasonable frequency limits (annual); SOC 2 Type II or ISO 27701 certification as primary compliance evidence with on-site audit as secondary; processor cooperation obligation; audit rights extend to sub-processors.

THE EDPB's CRITICAL POSITION: "RESTATING IS NEVER SUFFICIENT"
This is the single most important standard-setting statement for D8 scoring:
The guidelines now make clear that merely restating the requirements of Article 28 GDPR is never sufficient or appropriate when drafting a DPA: details of the procedures that the processor will follow must be included. Herbert Smith Freehills Kramer
The data processing agreement must not simply restate the provisions of the GDPR. Rather, the data processing agreement should include more specific and concrete information as to how the GDPR requirements will be met in practice. Hunton
Additional EDPB positions:

The EDPB emphasises that the controller will not be able to escape responsibility in cases where it agrees to non-negotiable terms offered by large service providers acting as processors, and the terms violate the GDPR requirements. Privacy World
When there is a need to modify the DPA, processors cannot simply publish a modified version on their website, but need to have the updated version approved by the relevant controllers. Similarly, relying on an online list of subprocessors to notify the controller only works if the list highlights which proposed subprocessor is new. The Data Advisor
Controllers, as part of their accountability obligation, should conduct due diligence to assess whether sub-processors provide sufficient guarantees. This assessment should be carried out at appropriate intervals, and not only at the onboarding stage. The Data Advisor


ENFORCEMENT ACTIONS SPECIFICALLY ON DPA FAILURES
Dedalus Biologie — €1.5M (France, April 2022):
No proper DPA was in place between Dedalus (processor) and its laboratory clients (controllers). The CNIL found that the company had extracted and migrated more personal data than required — exceeding controller instructions. The CNIL concluded that the processor alone may be held responsible for the absence of a data processing agreement. Orrick
This is landmark: the CNIL held the processor liable for the missing DPA, rejecting Dedalus's argument that the obligation lies equally with the controller.
Hessian DPA — Germany (Jan 2019): A shipping company was fined by the Hessian DPA specifically for a missing data processing agreement. Nathantrust
Aggregate enforcement data: According to the CMS Law GDPR Enforcement Tracker, insufficient data processing agreements have resulted in €1,128,510 in fines across 14 enforcement actions. HyperStart

HOW THE 2021 SCCs INTERACT WITH ART. 28
This is critical for scoring because many vendors will present their SCCs as their DPA:
For international transfers (Modules 2 and 3): The requirements of Article 28 of the GDPR have been incorporated into Module 2 (controller-to-processor) and Module 3 (processor-to-processor). Companies therefore do not need to sign a separate contract to comply with Article 28. European Commission
For intra-EEA processing: The EC also published separate Art. 28 SCCs that can be used as a DPA template for processing that doesn't involve international transfers. These are optional — vendors can use their own DPA.
The "gold-plating" in the EC Art. 28 SCCs: In places the EC Art. 28 SCCs go beyond what the law strictly requires. For example, Clause 7.6(e) compels both parties to disclose specific compliance documentation to the data protection authority on request. Annex III indicates that a high standard of detail will be required for TOMs and that a generic description will not be sufficient. Bird & Bird
The practical gap: In practice, DPAs go beyond the obligations of Article 28(3) and (4) and are still the main contractual instrument for engagements that do not require data transfer. Or-Hof Many vendors use SCCs for transfers but still need a DPA for intra-EEA processing and for matters not covered by the SCCs (liability caps, audit logistics, AI-specific provisions).
Scoring implications: A vendor that presents the 2021 SCCs (Module 2 or 3) as their DPA for international transfers meets the Art. 28 baseline — but may lack specificity on matters the SCCs delegate to the annexes. Bandit should evaluate whether the annexes are properly completed with specific information, not left blank or filled with generic text.

BOILERPLATE vs. WELL-DRAFTED: THE DIAGNOSTIC CHECKLIST
Based on EDPB guidance, enforcement actions, and practitioner analysis, here are the specific indicators:
Boilerplate Indicators (Score ≤ 3)
IndicatorWhy It's a ProblemDPA mirrors Art. 28 language verbatim without elaborationMerely restating Art. 28 is never sufficient Herbert Smith Freehills KramerNo processing description annex (or description is one generic paragraph)Failure to identify all types of personal data that processors might access ComplydogSecurity described as "appropriate measures" or "industry standard"Provides no enforceable standards LegalGPSSub-processor clause with no list, no notification period, no objection rightBelow EDPB recommended standardBreach notification as "without undue delay" with no SLA or content commitmentFails to operationalize Art. 33 assistanceDeletion clause says "at termination" with no timeframe or certificationFails to operationalize Art. 28(3)(g)Audit rights limited to "reasonable request" with no defined processBelow EDPB recommended standardNo separate treatment of international transfersInstructions should also cover international transfers Privacy WorldDPA is non-negotiable with no mechanism for controller-specific instructionsController still bears accountability risk
Well-Drafted Indicators (Score 4–5)
IndicatorWhy It MattersDetailed processing description annex (data categories, purposes, data subjects, duration)EDPB requirement for specificitySpecific TOMs in annex with change approval processEDPB requirement; EC Art. 28 SCC standardPublished sub-processor list with locations, roles, 30-day notice, objection+termination rightFull Art. 28(2)+(4) compliance with operational teethBreach notification with specific SLA (24–48 hrs) and Art. 33(3) content commitmentOperationalizes D5Category-specific retention and defined deletion timeframe with certificationOperationalizes D7DSAR assistance with defined SLA and technical capability commitmentOperationalizes D3Audit rights with defined process (documentation first, on-site fallback)Practical and EDPB-alignedCross-border transfer mechanisms specified with TIA commitmentOperationalizes D4AI/ML restriction clause (customer data not used for training without explicit consent)Addresses EU AI Act + FTC requirements; operationalizes D6Tailored to the specific processing context, not a template applied unchangedEDPB requirement that DPA reflects actual relationship

CCPA SERVICE PROVIDER AGREEMENTS vs. GDPR DPAs
ElementGDPR Art. 28 DPACCPA/CPRA Service Provider AgreementWhen requiredAlways, for any processor relationshipRequired for data not to be classified as a "sale" or "sharing"Consequence of absenceInfringement of GDPR; fines up to €10M / 2%Transfer deemed a "sale," triggering opt-out obligationsPurpose limitationProcess only on documented controller instructionsProhibit retaining/using/disclosing data for any purpose other than statedSub-processorsPrior authorization + right to object + flow-downNotify business of sub-contracting + same contractual obligationsCompliance monitoringAudit rights + compliance demonstrationRight to take reasonable steps to ensure consistent use + monitoring "at least once every 12 months"Compliance notificationProcessor must alert controller of unlawful instructionsService provider must notify business if it can no longer meet CCPA obligationsCertificationNot requiredContractors must certify they understand and will complyKey differenceController-instruction model; processor is agentPurpose-limitation model; service provider has more independence but narrower permitted uses
For Bandit scoring: A Score 5 DPA should address both GDPR Art. 28 and CCPA/CPRA service provider requirements, particularly since many vendor relationships span both jurisdictions. The certification requirement (CCPA-specific) and the monitoring-at-least-annually requirement are additive to the GDPR baseline.

AI-SPECIFIC DPA PROVISIONS FOR 2025+
Based on EU AI Act, FTC enforcement, and the EDPB's position on AI training data, a modern DPA should include:
Essential AI clause (any vendor using AI in service delivery):

Disclosure of whether and how AI systems are used in processing controller data
Commitment not to use controller data for AI model training without explicit written authorization
If AI training is authorized: specification of data categories, purposes, retention, and segregation commitments
Obligation to inform controller if AI Act obligations apply to the processing

Enhanced AI clause (vendors providing AI-powered services):

EU AI Act Art. 53 compliance commitments (if GPAI provider)
Training data governance documentation per Art. 10
Transparency obligations per Art. 50 (notification of AI interaction)
Human oversight provisions per Art. 14 (for high-risk AI)
Data provenance documentation commitment
Algorithmic disgorgement readiness (delete derived models if data consent withdrawn)


D8 SCORING RUBRIC — The Complete Specification
Score 1 — Absent or Non-Compliant

No DPA exists at all
OR: DPA exists but is missing 3+ of the 8 Art. 28(3) mandatory provisions
OR: DPA references outdated legal framework (e.g., pre-GDPR Data Protection Directive)
OR: DPA contains provisions that directly conflict with GDPR requirements (e.g., processor determines purposes of processing)

Regulatory basis: Direct infringement of Art. 28; the CNIL concluded that the processor alone may be held responsible for the absence of a DPA Orrick
Score 2 — Materially Deficient

DPA exists and addresses all 8 Art. 28(3) provisions, but only by restating the regulation verbatim
No processing description annex or only a generic one-paragraph description
Security measures described only as "appropriate" or "industry standard"
Sub-processor management with no published list or no notification mechanism
Missing at least one of: breach notification specifics, deletion timeframe, audit process definition
No treatment of international transfers
No CCPA/CPRA provisions despite processing California residents' data

Score 3 — Minimum Compliant

All 8 Art. 28(3) provisions present with some specificity beyond verbatim restatement
Processing description annex exists identifying data categories, purposes, and data subjects
Security measures described at a general level (e.g., "encryption, access controls, regular testing")
Sub-processor list exists (even if URL-based) with general authorization and some notification mechanism
Breach notification addressed but without specific SLA
Deletion at termination mentioned but without timeframe or certification
Audit rights present but vaguely defined
International transfers addressed at a general level
DPA is recognizably a template applied without significant tailoring to the specific relationship

This is where most vendor DPAs land. The EDPB says this is insufficient, but it meets the literal Art. 28 requirements.
Score 4 — Strong
All of Score 3, plus:

Processing description annex is detailed and tailored to the specific processing relationship
TOMs listed in a separate annex with change notification requirement
Sub-processor list with locations and roles; 30-day notification period; explicit objection right with defined consequences (termination right)
Breach notification with defined SLA (24–48 hours) and commitment to provide Art. 33(3) content
Deletion within specified timeframe (e.g., 30 days) with certification option
DSAR assistance with defined turnaround time
Audit rights with defined process (documentation-based + on-site fallback)
International transfer mechanisms specified (SCCs with module identified, DPF certification, or adequacy)
CCPA/CPRA service provider provisions included alongside GDPR terms
Supported by independent verification (SOC 2 Type II or ISO 27701 referenced)

Score 5 — Gold Standard
All of Score 4, plus:

DPA is demonstrably tailored to the specific processing context (not a template applied unchanged)
Includes AI/ML restriction clause: explicit prohibition on using controller data for model training without separate written authorization
Addresses EU AI Act obligations where applicable
Algorithmic disgorgement readiness commitment
Category-specific retention schedules linked to purposes (not blanket retention)
Sub-processor changes include updated TIA where applicable
Addresses derived/aggregated data treatment at termination
DPA is version-controlled with change log
Includes measurable commitments (SLAs for breach notification, DSAR response, deletion)
Supported by SOC 2 Type II with Privacy TSC AND/OR ISO 27701 certification as evidence that DPA commitments are operationally implemented
Addresses backup copy deletion explicitly
Includes controller's right to receive regular compliance reports without requiring audit


HOW D8 QUALITY SETS THE CEILING FOR D2, D5, AND D7
This is the critical architectural insight for Bandit:
If D8 scores...D2 ceilingD5 ceilingD7 ceilingRationale1222Without a DPA, sub-processor, breach, and retention commitments are unenforceable aspirational statements2333A boilerplate DPA caps the operational specificity of dependent dimensions3444A minimum-compliant DPA allows dimensions to score higher based on policy language, but lacks the contractual teeth for a 54–5555A well-drafted DPA removes the contractual ceiling; dimensions can score on their own merits
The logic: A privacy policy that promises 24-hour breach notification (excellent D5 language) but sits on top of a DPA that says "without undue delay" (generic D8 language) creates an enforceability gap. The contractual commitment in the DPA is what the controller can actually rely on in a dispute. Bandit should flag these policy-DPA mismatches.

DPA QUALITY CHECKLIST — For Bandit's Automated Assessment
When Bandit evaluates a DPA, it should check for these specific elements in order:
Structural completeness (binary — present or absent):

Processing description annex (subject matter, duration, nature/purpose, data types, data subject categories)
Art. 28(3)(a) — documented instructions clause
Art. 28(3)(b) — confidentiality clause
Art. 28(3)(c) — security measures clause
Art. 28(3)(d) — sub-processor clause
Art. 28(3)(e) — DSAR assistance clause
Art. 28(3)(f) — Arts. 32–36 assistance clause
Art. 28(3)(g) — deletion/return clause
Art. 28(3)(h) — audit/compliance clause

Specificity assessment (graduated — boilerplate to gold standard):
10. Are instructions documented in an annex or just referenced generically?
11. Does the security clause include specific TOMs or just say "appropriate measures"?
12. Does the sub-processor clause include a published list, notification period, and objection mechanism?
13. Does the breach clause include a specific SLA and Art. 33(3) content commitment?
14. Does the deletion clause include a timeframe and certification mechanism?
15. Does the audit clause include a defined process?
Modern provisions (presence signals Score 4–5):
16. International transfer mechanism specified
17. CCPA/CPRA service provider provisions
18. AI/ML data usage restriction clause
19. Category-specific retention schedules
20. Measurable SLAs (not just "reasonable" or "without undue delay")
]

