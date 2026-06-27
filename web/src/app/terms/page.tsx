import type { Metadata } from "next";
import { PageHero, Prose } from "@/components/site/page-parts";

export const metadata: Metadata = {
  title: "Terms of Service — AgentMesh",
  description: "The terms that govern your use of AgentMesh.",
};

const updated = "January 1, 2026";

export default function TermsPage() {
  return (
    <>
      <PageHero eyebrow="Legal" title="Terms of Service" description={`Last updated ${updated}.`} />
      <Prose>
        <p>
          These Terms of Service govern your access to and use of the AgentMesh
          website and platform. This is a template for the buildathon and should
          be reviewed by counsel before production use.
        </p>

        <h2>Use of the Service</h2>
        <p>
          You agree to use the platform lawfully and not to misuse it, interfere
          with its operation, or attempt to access it in unauthorized ways.
        </p>

        <h2>Autonomous Actions &amp; Oversight</h2>
        <p>
          AgentMesh enables AI agents to analyze, decide, and execute actions.
          Critical or irreversible actions are gated by human approval. You are
          responsible for the policies, permissions, and approvals you configure.
        </p>

        <h2>On-Chain Transactions</h2>
        <p>
          Actions executed on the Casper Network are irreversible. You are
          responsible for funds, keys, and spending limits associated with your
          organizations.
        </p>

        <h2>No Warranty</h2>
        <p>
          The service is provided &ldquo;as is&rdquo; without warranties of any
          kind. We do not guarantee that outputs are error-free.
        </p>

        <h2>Limitation of Liability</h2>
        <p>
          To the maximum extent permitted by law, AgentMesh is not liable for
          indirect, incidental, or consequential damages arising from use of the
          service.
        </p>

        <h2>Contact</h2>
        <p>
          Questions about these terms? Email{" "}
          <a href="mailto:legal@agentmesh.world">legal@agentmesh.world</a>.
        </p>
      </Prose>
    </>
  );
}
