import PageShell from "../../components/layout/PageShell";
import { PageHeader } from "../../components/ui/StateViews";
import { ChangePasswordSection, ProfileSection, SettingsSection } from "./AccountSections";
import EditorSettings from "./EditorSettings";

export default function Settings() {
  return (
    <PageShell maxWidth="max-w-3xl">
      <PageHeader eyebrow="Account" title="Settings" description="Your profile, editor preferences and account security." />

      <div className="space-y-5 pb-6">
        <ProfileSection />
        <EditorSettings />
        <ChangePasswordSection />
        <SettingsSection id="privacy-heading" title="Privacy and session security">
          <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-text-muted">
            <li>Your session is stored in this browser only and ends when you sign out or it expires.</li>
            <li>
              In graded workspaces, only counts of tab switches, blocked pastes and similar events are recorded — never
              your clipboard contents, keystrokes, screen, camera or microphone.
            </li>
            <li>These indicators help your instructor review work; they are not automatic findings of misconduct.</li>
            <li>Use Sign out on shared or public computers.</li>
          </ul>
        </SettingsSection>
      </div>
    </PageShell>
  );
}
