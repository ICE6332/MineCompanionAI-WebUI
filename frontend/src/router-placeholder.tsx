// TanStack Router 占位适配：用 react-router-dom 提供最小兼容接口
import {
  Link as ReactRouterLink,
  type LinkProps as ReactRouterLinkProps,
  useLocation as useReactRouterLocation,
} from "react-router-dom";

export interface LinkProps extends ReactRouterLinkProps {
  disabled?: boolean;
}

export function Link(props: LinkProps) {
  const { disabled, ...rest } = props;
  if (disabled) {
    return (
      <span aria-disabled="true" className="cursor-not-allowed opacity-60">
        {rest.children}
      </span>
    );
  }
  return <ReactRouterLink {...rest} />;
}

export function useLocation<T = { href: string }>(options?: {
  select?: (location: { href: string }) => T;
}): T {
  const loc = useReactRouterLocation();
  const hrefObj = { href: window.location.origin + loc.pathname + loc.search };
  if (options?.select) {
    return options.select(hrefObj as any);
  }
  return hrefObj as any;
}
