"use client";

import { FormEvent, ReactNode } from "react";

type InputBoxProps = {
  value: string;
  disabled?: boolean;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  children?: ReactNode;
};

export function InputBox({ value, disabled = false, onChange, onSubmit, children }: InputBoxProps) {
  return (
    <form
      onSubmit={onSubmit}
      className="rounded-[32px] border border-white/12 bg-white/8 p-3 shadow-panel backdrop-blur-2xl transition duration-300"
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-end">
        <label className="flex-1">
          <span className="sr-only">Describe symptoms</span>
          <textarea
            value={value}
            disabled={disabled}
            onChange={(event) => onChange(event.target.value)}
            placeholder="Tell me what you’re feeling in your own words"
            className="min-h-28 w-full resize-none rounded-[24px] border border-white/8 bg-[#0E141C] px-5 py-4 text-base leading-7 text-white outline-none transition placeholder:text-slate-500 focus:border-sky-400/50 disabled:opacity-60"
          />
        </label>

        <div className="flex items-center gap-3">{children}</div>
      </div>
    </form>
  );
}
