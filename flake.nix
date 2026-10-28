{
  description = "playwright_figure_tests dev shell (provides Playwright browsers for NixOS)";

  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    nixpkgs.url = "github:nixos/nixpkgs";
  };

  outputs = { flake-parts, ... } @ inputs: flake-parts.lib.mkFlake { inherit inputs; } {
    perSystem = { config, self', inputs', pkgs, system, ... }: {
      devShells.default = pkgs.mkShell {
        # playwright-driver.browsers provides Firefox/Chromium patched
        # to run on NixOS. The pip `playwright` package reads
        # PLAYWRIGHT_BROWSERS_PATH and uses these browsers directly;
        # its version must match whatever nixpkgs pins here.
        packages = with pkgs; [
          bash
          playwright-driver.browsers
        ];

        shellHook = ''
          export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
          export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
          # Browsers installed by nix so no-op the install command in tox
          export PLAYWRIGHT_INSTALL_CMD="python -c pass"
        '';
      };
    };
    systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
  };
}
