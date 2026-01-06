-- Services
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Anim = {}

function Anim.Load(humanoid)
	-- ===== Animator =====
	local animator = humanoid:FindFirstChildOfClass("Animator")
	if not animator then
		animator = Instance.new("Animator")
		animator.Parent = humanoid
	end

	-- ===== Animation Assets =====
	local A = ReplicatedStorage:WaitForChild("Animations")

	-- ===== LOAD ANIMATIONS (???????????????) =====

	-- Walk
	local walkFront = animator:LoadAnimation(A.FrontWalkAnim)
	local walkBack  = animator:LoadAnimation(A.BackWalkAnim)
	local walkLeft  = animator:LoadAnimation(A.LeftWalkAnim)
	local walkRight = animator:LoadAnimation(A.RightWalkAnim)

	-- Actions
	local sprintAnim = animator:LoadAnimation(A.SprintAnim)
	local slideAnim  = animator:LoadAnimation(A.SlideAnim)
	local landAnim   = animator:LoadAnimation(A.LandAnim)

	-- Roll
	local rollFront = animator:LoadAnimation(A.FrontRollAnim)
	local rollBack  = animator:LoadAnimation(A.BackRollAnim)
	local rollLeft  = animator:LoadAnimation(A.LeftRollAnim)
	local rollRight = animator:LoadAnimation(A.RightRollAnim)

	-- Vault
	local vaultAnim = animator:LoadAnimation(A.VaultAnim)

	-- Wall Run (???????????????????????? Explorer ??? 3 ???????????)
	local wrLeft = animator:LoadAnimation(A.WallRunLeftAnim) 
	local wrRight = animator:LoadAnimation(A.WallRunRightAnim)

	local LedgeIdle = animator:LoadAnimation(A.LedgeIdleAnim)
	local LedgeClimb = animator:LoadAnimation(A.LedgeClimbAnim)
	
	local Freeze = animator:LoadAnimation(A.FreezeAnim)
	-- ===== CONFIGURATION (??????? Priority & Loop) =====

	freezeAnims.Freeze.Priority = Enum.AnimationPriority.Action

	-- Movement
	sprintAnim.Priority = Enum.AnimationPriority.Movement

	-- Actions
	slideAnim.Priority  = Enum.AnimationPriority.Action
	landAnim.Priority   = Enum.AnimationPriority.Action

	-- Roll
	rollFront.Priority = Enum.AnimationPriority.Action
	rollBack.Priority  = Enum.AnimationPriority.Action
	rollLeft.Priority  = Enum.AnimationPriority.Action
	rollRight.Priority = Enum.AnimationPriority.Action

	-- Vault
	vaultAnim.Priority = Enum.AnimationPriority.Action
	vaultAnim.Looped = false

	-- Wall Run (?????: ???? Priority ??????? Movement)
	wrLeft.Priority = Enum.AnimationPriority.Action
	wrLeft.Looped = true

	wrRight.Priority = Enum.AnimationPriority.Action
	wrRight.Looped = true
	
	LedgeIdle.Priority = Enum.AnimationPriority.Action
	LedgeIdle.Looped = true -- ????????????????

	LedgeClimb.Priority = Enum.AnimationPriority.Action
	LedgeClimb.Looped = false -- ??????????????????

	-- ===== RETURN TABLE =====
	-- ???????????????????????????? (???? LoadAnimation ????????)
	return {
		Walk = {
			Front = walkFront,
			Back  = walkBack,
			Left  = walkLeft,
			Right = walkRight,
		},

		Sprint = sprintAnim,
		Slide  = slideAnim,
		Land   = landAnim,

		Roll = {
			Front = rollFront,
			Back  = rollBack,
			Left  = rollLeft,
			Right = rollRight,
		},

		Vault = {
			vaultAnim
		},

		WallRun = {
			Left  = wrLeft,  -- ????????? wrLeft ?????????? Priority ????
			Right = wrRight, -- ????????? wrRight
		
		},
		
		Ledge = {
			Idle = LedgeIdle,
			Climb = LedgeClimb,
		}
	}
end

return Anim