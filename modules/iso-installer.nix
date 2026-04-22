{
  inputs,
  self,
  ...
}: let
  installerSystem = inputs.nixpkgs.lib.nixosSystem {
    system = "x86_64-linux";
    specialArgs = {nixvibeSource = inputs.nixvibeSource;};
    modules = [self.nixosModules.nixvibeInstaller];
  };
in {
  flake.nixosConfigurations = {
    nixvibeInstaller = installerSystem;
    "nixvibe-installer" = installerSystem;
  };

  flake.nixosModules.nixvibeInstaller = {
    config,
    lib,
    pkgs,
    modulesPath,
    nixvibeSource,
    ...
  }: let
    system = pkgs.stdenv.hostPlatform.system;
    codexPkg = inputs.codex-cli-nix.packages.${system}.default;
    claudePkg = inputs.claude-code.packages.${system}.default;
    mcpNixosPkg = inputs.mcp-nixos.packages.${system}.default;
    carlMcpPkg = pkgs.buildNpmPackage {
      pname = "carl-mcp";
      version = "2.0.0";
      src = nixvibeSource + "/.agents/carl/runtime/carl-mcp";
      npmDepsHash = "sha256-Tih4EgNul3QukVPSz1m4Nkzp65b9j0KTufp0Iqzcr2U=";
      nativeBuildInputs = [pkgs.makeWrapper];
      dontNpmBuild = true;
      installPhase = ''
        runHook preInstall
        mkdir -p $out/lib/carl-mcp
        cp -r . $out/lib/carl-mcp
        makeWrapper ${pkgs.nodejs}/bin/node $out/bin/carl-mcp \
          --add-flags "$out/lib/carl-mcp/index.js"
        runHook postInstall
      '';
    };
    welcomeScript = pkgs.writeShellScript "nixvibe-assistant-welcome.sh" ''
      clear
      cat <<'EOF'
      ------------------------------------------------------------
      Welcome to the NixVibe Installer Live Environment
      ------------------------------------------------------------

      Assistant CLIs are preinstalled:
        - codex   (OpenAI Codex CLI)
        - claude  (Anthropic Claude Code CLI)

      Account requirements:
        - codex: ChatGPT account (or OpenAI API key)
        - claude: Claude account with Claude Code access

      Project bundle:
        - /nixvibe

      Quick start:
        1) cd /nixvibe
        2) codex    # or: claude

      SSH access (for VM convenience):
        - host service: enabled
        - user: root
        - password: nixvibe
        - recommended: run 'passwd' immediately after login

      EOF
      exec ${pkgs.bashInteractive}/bin/bash -i
    '';
  in {
    imports = [(modulesPath + "/installer/cd-dvd/installation-cd-graphical-gnome.nix")];

    image.baseName = lib.mkForce
      "nixvibe-nixos-gnome-${config.system.nixos.label}-${pkgs.stdenv.hostPlatform.system}";

    nixpkgs.config.allowUnfreePredicate = pkg: builtins.elem (lib.getName pkg) ["claude-code"];

    services.desktopManager.gnome.extraGSettingsOverrides = ''
      [org.gnome.shell]
      welcome-dialog-last-shown-version='9999999999'
    '';

    nix.settings.experimental-features = ["nix-command" "flakes"];

    environment.systemPackages = [
      codexPkg
      claudePkg
      mcpNixosPkg
      carlMcpPkg
      pkgs.bubblewrap
      pkgs.git
      pkgs.nodejs
      pkgs.python3
      pkgs.ripgrep
      pkgs.jq
    ];

    services.qemuGuest.enable = true;
    services.spice-vdagentd.enable = true;
    services.openssh = {
      enable = lib.mkForce true;
      openFirewall = lib.mkForce true;
      settings = {
        PermitRootLogin = lib.mkForce "yes";
        PasswordAuthentication = lib.mkForce true;
      };
    };

    users.users.root = {
      initialHashedPassword = lib.mkForce null;
      initialPassword = lib.mkForce "nixvibe";
    };

    isoImage.contents = [
      {
        source = lib.cleanSource nixvibeSource;
        target = "/nixvibe";
      }
    ];

    systemd.services.nixvibe-live-copy = {
      description = "Copy bundled nixvibe tree into /nixvibe";
      wantedBy = ["multi-user.target"];
      before = ["display-manager.service"];
      after = ["local-fs.target"];
      unitConfig.ConditionPathExists = "/iso/nixvibe";

      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
      };

      script = ''
        mkdir -p /nixvibe
        cp -a --no-preserve=ownership /iso/nixvibe/. /nixvibe/
        chmod -R u+rwX,go+rX /nixvibe
        mkdir -p /nixvibe/.agents/carl/runtime/carl-mcp
        ln -sfn ${carlMcpPkg}/lib/carl-mcp/node_modules \
          /nixvibe/.agents/carl/runtime/carl-mcp/node_modules
      '';
    };

    environment.etc."xdg/autostart/nixvibe-welcome.desktop".text = ''
      [Desktop Entry]
      Type=Application
      Version=1.0
      Name=NixVibe Assistant Welcome
      Comment=Open an assistant onboarding terminal at login
      Exec=${pkgs.gnome-console}/bin/kgx -- ${welcomeScript}
      X-GNOME-Autostart-enabled=true
      NoDisplay=true
    '';
  };

  flake.packages.x86_64-linux = let
    isoImage = installerSystem.config.system.build.isoImage;
  in {
    default = isoImage;
    iso = isoImage;
    isoInstaller = isoImage;
    "iso-installer" = isoImage;
  };
}
