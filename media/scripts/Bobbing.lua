-- Bobbing.lua (ModuleScript)

local RunService = game:GetService("RunService")

local Bobbing = {}

local connection

function Bobbing:Enable(ctx)
	if connection then
		connection:Disconnect()
	end

	connection = RunService.RenderStepped:Connect(function()
		local hum = ctx.Humanoid
		local CT = tick()

		if hum.MoveDirection.Magnitude > 0 then
			local bobX = math.cos(CT * 10) * 0.35
			local bobY = math.abs(math.sin(CT * 10)) * 0.35
			local bob = Vector3.new(bobX + 2, bobY, 0.35)

			hum.CameraOffset = hum.CameraOffset:Lerp(bob, 0.35)
		else
			hum.CameraOffset =
				Vector3.new(2, hum.CameraOffset.Y, hum.CameraOffset.Z)
				* Vector3.new(1, 0.75, 0.75)
		end
	end)
end

function Bobbing:Disable()
	if connection then
		connection:Disconnect()
		connection = nil
	end
end

return Bobbing
