import { useEffect, useRef, useState } from "react";

interface AnimatedNumberProps {
  value: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  className?: string;
  formatter?: (value: number) => string;
}

export function AnimatedNumber({
  value,
  duration = 1000,
  prefix = "",
  suffix = "",
  decimals = 0,
  className = "",
  formatter,
}: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const startTimeRef = useRef<number>(0);
  const startValueRef = useRef(0);
  const animationRef = useRef<number>(0);
  const prevValueRef = useRef(0);

  useEffect(() => {
    startValueRef.current = prevValueRef.current;
    startTimeRef.current = performance.now();
    prevValueRef.current = value;

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing: ease-out-cubic
      const easeOut = 1 - Math.pow(1 - progress, 3);
      
      const current = startValueRef.current + (value - startValueRef.current) * easeOut;
      setDisplayValue(current);

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [value, duration]);

  const formattedValue = formatter
    ? formatter(displayValue)
    : displayValue.toFixed(decimals);

  return (
    <span className={`count-up ${className}`}>
      {prefix}
      {formattedValue}
      {suffix}
    </span>
  );
}
