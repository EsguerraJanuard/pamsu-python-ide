import { useState } from "react";

import PageShell from "../../components/layout/PageShell";
import { InlineAlert, PageHeader } from "../../components/ui/StateViews";
import api, { getErrorMessage } from "../../services/api";
import { AST_STRICTNESS_LEVELS } from "../../utils/astRules";
import { useAuth } from "../auth/AuthContext";
import { ChangePasswordSection, ProfileSection, SettingsSection } from "./AccountSections";
import StrictnessPicker from "./StrictnessPicker";

function EvaluationPreferences() {
  const { user, updateUser } = useAuth();
  const savedStrictness = user?.ast_strictness_level || "";
  const [strictness, setStrictness] = useState(savedStrictness);
  const isDirty = strictness !== savedStrictness;
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
      <form onSubmit={handleSave} noValidate className="space-y-5">
        <StrictnessPicker
          name="ast-strictness"
          legend="AST strictness"
          description="Choose how the structure check counts the required structures in your activities."
          value={strictness}
          onChange={(value) => {
            setStrictness(value);
            setMessage(null);
          }}
          disabled={isSaving}
        />
        <div className="flex flex-col gap-3 border-t border-border-subtle pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-text-muted">
            {!savedStrictness
              ? "No level saved yet: the MIS default is used until you save one here."
              : isDirty
                ? "Unsaved change."
                : `Saved level: ${AST_STRICTNESS_LEVELS.find((level) => level.value === savedStrictness)?.label ?? savedStrictness}.`}
          </p>
          <button type="submit" disabled={isSaving || !strictness || !isDirty} className="btn-primary w-full sm:w-auto">
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
