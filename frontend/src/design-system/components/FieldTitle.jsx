import React from "react";

export function FieldTitle({ title, tip, className = "" }) {
  return (
    <div className={`ds-field-title${className ? ` ${className}` : ""}`}>
      <span>{title}</span>
      {tip ? (
        <span className="tip-badge" title={tip} aria-label={tip}>
          i
        </span>
      ) : null}
    </div>
  );
}
