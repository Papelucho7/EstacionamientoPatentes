CREATE TABLE Vehiculos (
    Patente NVARCHAR(10) PRIMARY KEY,
    Estado NVARCHAR(10) NOT NULL CHECK (Estado IN ('Dentro', 'Fuera')),
    UltimoMovimiento DATETIME NOT NULL,
    RUT_Persona NVARCHAR(12) NULL,
    CONSTRAINT FK_Vehiculo_Persona FOREIGN KEY (RUT_Persona) REFERENCES Persona(RUT)
);

CREATE TABLE Movimientos (
    ID INT PRIMARY KEY IDENTITY(1,1),
    Patente NVARCHAR(10) NOT NULL,
    TipoMovimiento NVARCHAR(10) NOT NULL CHECK (TipoMovimiento IN ('Entrada', 'Salida')),
    FechaHora DATETIME NOT NULL
);

CREATE TABLE Rol (
    ID INT PRIMARY KEY IDENTITY(1,1),
    Nombre NVARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Persona (
    RUT NVARCHAR(12) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL,
    Apellido NVARCHAR(100) NOT NULL,
    Telefono NVARCHAR(20) NULL,
    ID_Rol INT NULL,
    Activo BIT NOT NULL DEFAULT 1,
    CONSTRAINT FK_Persona_Rol FOREIGN KEY (ID_Rol) REFERENCES Rol(ID)
);


