import { headers } from "next/headers";
import { ShieldCheck, Ban, Trash2, ShieldOff } from "lucide-react";
import { auth } from "@/lib/auth";
import { getSession } from "@/lib/session";
import {
  setUserRoleAction,
  setUserBanAction,
  deleteUserAction,
} from "@/app/admin/actions";
import { CreateUserForm } from "./create-user-form";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

type UserRow = {
  id: string;
  name: string;
  email: string;
  role?: string | null;
  banned?: boolean | null;
  createdAt: string | Date;
};

const fmt = new Intl.DateTimeFormat("en-US", { dateStyle: "medium" });

export default async function AdminUsersPage() {
  const session = await getSession();
  const currentId = session?.user.id;

  let users: UserRow[] = [];
  try {
    const res = await auth.api.listUsers({
      query: { limit: 200, sortBy: "createdAt", sortDirection: "desc" },
      headers: await headers(),
    });
    users = (res?.users ?? []) as UserRow[];
  } catch (error) {
    console.error("[admin] listUsers failed:", error);
  }

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-8">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          Users & Roles
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage who can access the admin. {users.length} user
          {users.length === 1 ? "" : "s"}.
        </p>
      </header>

      <CreateUserForm />

      <div className="mt-6 overflow-hidden rounded-xl border border-border">
        <div className="hidden grid-cols-[1fr_auto_auto_auto] gap-4 border-b border-border bg-card px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground sm:grid">
          <span>User</span>
          <span>Role</span>
          <span>Joined</span>
          <span className="text-right">Actions</span>
        </div>

        {users.length === 0 ? (
          <p className="bg-card px-5 py-10 text-center text-sm text-muted-foreground">
            No users found.
          </p>
        ) : (
          users.map((u, i) => {
            const isAdmin = u.role === "admin";
            const isSelf = u.id === currentId;
            return (
              <div
                key={u.id}
                className={cn(
                  "grid grid-cols-1 gap-3 bg-card px-5 py-4 sm:grid-cols-[1fr_auto_auto_auto] sm:items-center sm:gap-4",
                  i !== 0 && "border-t border-border",
                )}
              >
                <div className="min-w-0">
                  <p className="flex items-center gap-2 truncate text-sm font-medium text-foreground">
                    {u.name}
                    {isSelf && (
                      <span className="rounded bg-secondary px-1.5 py-0.5 text-[10px] text-muted-foreground">
                        You
                      </span>
                    )}
                    {u.banned && (
                      <span className="rounded bg-destructive/15 px-1.5 py-0.5 text-[10px] font-semibold text-destructive">
                        Banned
                      </span>
                    )}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {u.email}
                  </p>
                </div>

                <span
                  className={cn(
                    "inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider",
                    isAdmin
                      ? "bg-brand/15 text-brand"
                      : "bg-secondary text-muted-foreground",
                  )}
                >
                  {isAdmin && <ShieldCheck className="size-3" />}
                  {u.role ?? "user"}
                </span>

                <span className="text-xs text-muted-foreground">
                  {fmt.format(new Date(u.createdAt))}
                </span>

                <div className="flex items-center justify-start gap-1.5 sm:justify-end">
                  {!isSelf && (
                    <>
                      <form action={setUserRoleAction}>
                        <input type="hidden" name="userId" value={u.id} />
                        <input
                          type="hidden"
                          name="role"
                          value={isAdmin ? "user" : "admin"}
                        />
                        <button
                          type="submit"
                          title={isAdmin ? "Demote to user" : "Promote to admin"}
                          className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border px-2.5 text-xs text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                        >
                          {isAdmin ? (
                            <ShieldOff className="size-3.5" />
                          ) : (
                            <ShieldCheck className="size-3.5" />
                          )}
                          {isAdmin ? "Demote" : "Make admin"}
                        </button>
                      </form>

                      <form action={setUserBanAction}>
                        <input type="hidden" name="userId" value={u.id} />
                        <input
                          type="hidden"
                          name="ban"
                          value={u.banned ? "0" : "1"}
                        />
                        <button
                          type="submit"
                          title={u.banned ? "Unban" : "Ban"}
                          className="inline-flex size-8 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                        >
                          <Ban className="size-3.5" />
                        </button>
                      </form>

                      <form action={deleteUserAction}>
                        <input type="hidden" name="userId" value={u.id} />
                        <button
                          type="submit"
                          title="Delete user"
                          className="inline-flex size-8 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:border-destructive/40 hover:bg-destructive/10 hover:text-destructive"
                        >
                          <Trash2 className="size-3.5" />
                        </button>
                      </form>
                    </>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
