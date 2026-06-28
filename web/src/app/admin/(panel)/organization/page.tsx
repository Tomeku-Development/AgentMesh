import { OrganizationManager } from "./organization-manager";

export const dynamic = "force-dynamic";

export default function AdminOrganizationPage() {
  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-8">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          Organization
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage the Better Auth organization used for admin workspaces and
          integrations.
        </p>
      </header>

      <OrganizationManager />
    </div>
  );
}
