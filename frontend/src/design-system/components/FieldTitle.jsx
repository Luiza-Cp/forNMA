import React from "react";
import { Tip } from "./Tip.jsx";

export function FieldTitle({ title, tip, className = "" }) {
  return (
    <div className={`ds-field-title${className ? ` ${className}` : ""}`}>
      <span>{title}</span>
      {tip ? <Tip text={tip} /> : null}
    </div>
  );
}
