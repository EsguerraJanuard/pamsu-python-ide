import { useState } from "react";

import PageShell from "../../components/layout/PageShell";
import CustomSelect from "../../components/ui/CustomSelect";
import { InlineAlert, PageHeader } from "../../components/ui/StateViews";
import api, { getErrorMessage } from "../../services/api";
import { useAuth } from "../auth/AuthContext";
import { ChangePasswordSection, ProfileSection, SettingsSection } from "./AccountSections";

const STRICTNESS_OPTIONS = [
  { value: "lax", label: "Lenient — focus on execution output" },
  { value: "moderate", label: "Moderate — standard structural checks" },
  { value: "strict", label: "Strict — enforce required structures rigidly" },
];

function EvaluationPreferences() {
  const { user, updateUser } = useAuth();
  const [strictness, setStrictness] = useState(user?.ast_strictness_level || "");
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const handleSave = async (event) => {
    event.preventDefault();
    if (!strictness) {
      setMessage({ tone: "error", text: "Choose a strictness level first." });
      return;
    }
    setIsSaving(true);
    setMessage(null);
    try {
      const updated = await api.patch("/users/me", {
        name: user?.name,
        ast_strictness_level: strictness,
      });
      updateUser({ ...user, ast_strictness_level: updated?.ast_strictness_level || strictness });
      setMessage({ tone: "success", text: "AST strictness saved. It applies to new structure checks on your activities." });
    } catch (err) {
      setMessage({ tone: "error", text: getErrorMessage(err, "The preference could not be saved.") });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <SettingsSection
      id="evaluation-heading"
      title="Evaluation preferences"
      description="How strictly the AST checker evaluates required code structures in your activities."
    >
      {message && (
        <InlineAlert tone={message.tone} onDismiss={() => setMessage(null)} className="mb-4">
          {message.text}
        </InlineAlert>
      )}
      <form onSubmit={handleSave} noValidate className="space-y-4">
        <div>
          <label htmlFor="ast-strictness" className="field-label">
            AST strictness
          </label>
          <CustomSelect
            id="ast-strictness"
            value={strictness}
            onChange={setStrictness}
            options={STRICTNESS_OPTIONS}
            placeholder="Select a strictness level"
            disabled={isSaving}
          />
          {!user?.ast_strictness_level && (
            <p className="mt-1.5 text-xs text-text-muted">
              Your current level isn&apos;t shown until you save one here. The server default is used until then.
            </p>
          )}
        </div>
        <div className="flex justify-end">
          <button type="submit" disabled={isSaving || !strictness} className="btn-primary">
            {isSaving ? "Saving…" : "Save preference"}
          </button>
        </div>
      </form>
    </SettingsSection>
  );
}

export default function InstructorSettings() {
  return (
    <PageShell role="instructor" maxWidth="max-w-3xl">
      <PageHeader eyebrow="Account" title="Settings" description="Your faculty profile, evaluation preferences and account security." />
      <div className="space-y-5 pb-6">
        <ProfileSection />
        <EvaluationPreferences />
        <ChangePasswordSection />
      </div>
    </PageShell>
  );
}
