import type { Metadata } from "next";
import { PageHero, Prose } from "@/components/site/page-parts";

export const metadata: Metadata = {
  title: "Privacy Policy — AgentMesh",
  description: "How AgentMesh collects, uses, and protects your information.",
};

const updated = "January 1, 2026";

export default function PrivacyPage() {
  return (
    <>
      <PageHero eyebrow="Legal" title="Privacy Policy" description={`Last updated ${updated}.`} />
      <Prose>
        <p>
          This Privacy Policy explains how AgentMesh (&ldquo;we&rdquo;) collects,
          uses, and safeguards information when you use our website and platform.
          This is a template for the buildathon and should be reviewed by counsel
          before production use.
        </p>

        <h2>Information We Collect</h2>
        <ul>
          <li>
            <strong>Contact information</strong> you provide via forms (name,
            email, company, message).
          </li>
          <li>
            <strong>Account &amp; usage data</strong> needed to operate the
            platform and your organizations.
          </li>
          <li>
            <strong>Technical data</strong> such as logs and analytics used to
            keep the service reliable and secure.
          </li>
        </ul>

        <h2>How We Use Information</h2>
        <ul>
          <li>To provide, maintain, and improve the platform.</li>
          <li>To respond to inquiries and provide support.</li>
          <li>To secure the service and prevent abuse.</li>
        </ul>

        <h2>On-Chain Data</h2>
        <p>
          Decisions and actions recorded on the Casper Network are public and
          immutable by design. Do not submit sensitive personal data intended to
          remain private into on-chain workflows.
        </p>

        <h2>Data Retention</h2>
        <p>
          We retain information only as long as necessary for the purposes
          described here or as required by law.
        </p>

        <h2>Your Rights</h2>
        <p>
          Depending on your jurisdiction, you may have rights to access, correct,
          or delete your personal information. Contact us to exercise them.
        </p>

        <h2>Contact</h2>
        <p>
          Questions about this policy? Email{" "}
          <a href="mailto:privacy@agentmesh.world">privacy@agentmesh.world</a>.
        </p>
      </Prose>
    </>
  );
}
